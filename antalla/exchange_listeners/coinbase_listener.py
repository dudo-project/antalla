import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets
import aiohttp
import asyncio

from .. import db
from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

@ExchangeListener.register("coinbase")
class CoinbaseListener(WebsocketListener):
    def __init__(self,
                 exchange,
                 on_event,
                 markets=settings.COINBASE_MARKETS,
                 ws_url=settings.COINBASE_WS_URL,
                 session=db.session,
                 event_type=None):
        super().__init__(exchange, on_event, markets, ws_url, session=session, event_type=event_type)
        self._all_symbols = []
        self._format_markets()
        self.running = False
        self.last_update_ids = self._get_last_update_ids()
        

    def _get_last_update_ids(self):
        """fetches for each market the last update id from db and stores it in dict
        """
        last_update_ids = {}
        market_update_ids = self.session.execute(
            """
            select ex.name exchange, buy_sym_id, sell_sym_id, max(last_update_id) max_update_id
            from aggregate_orders
            inner join exchanges ex on aggregate_orders.exchange_id = ex.id where ex.name = 'coinbase'
            group by buy_sym_id, sell_sym_id, ex.name;
            """
        )
        for market in list(market_update_ids):
            last_update_id = market["max_update_id"] if market["max_update_id"] is not None else 0
            key = str(market["exchange"])+str(market["buy_sym_id"])+str(market["sell_sym_id"])
            logging.debug("KEY: {}, UPDATE_ID: {}".format(key, last_update_id))
            last_update_ids[key] = last_update_id
        return last_update_ids

    def _parse_message(self, message):
        event, payload = message["type"], message
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_snapshot(self, snapshot):
        agg_orders = []
        buy_sym_id, sell_sym_id = snapshot["product_id"].split("-")
        timestamp = datetime.now()
        order_info = dict(
            timestamp=timestamp,
            exchange_id=self.exchange.id,
            buy_sym_id=buy_sym_id,
            sell_sym_id=sell_sym_id
        )
        #TODO: remove if statement below
        market_key = self.exchange.name.lower() + buy_sym_id.upper() + sell_sym_id.upper()
        if market_key not in self.last_update_ids.keys():
            self.last_update_ids[market_key] = 0
        bids = self._create_agg_orders("bid", order_info, snapshot["bids"])
        asks = self._create_agg_orders("ask", order_info, snapshot["asks"])
        agg_orders.extend(bids)
        agg_orders.extend(asks)
        if len(agg_orders) > 0:
            self.last_update_ids[market_key] += 1   
        logging.debug(" {} - aggregated order book snapshot - agg orders: {}".format(self.exchange.name, len(agg_orders)))
        return [actions.InsertAction(agg_orders)]

    def _create_agg_orders(self, order_type, order_info, orders):
        parsed_orders = []
        market_key = self.exchange.name.lower() + order_info["buy_sym_id"].upper() + order_info["sell_sym_id"].upper()
        for order in orders:
            parsed_orders.append(models.AggOrder(
                timestamp=order_info["timestamp"],
                exchange_id=self.exchange.id,
                order_type=order_type,
                price=float(order[0]),
                size=float(order[1]),
                buy_sym_id=order_info["buy_sym_id"],
                sell_sym_id=order_info["sell_sym_id"],
                last_update_id=self.last_update_ids[market_key]
            ))      
        return parsed_orders

    # TODO: add check for valid market
    def _parse_l2update(self, update):
        agg_orders = []
        buy_sym_id, sell_sym_id = update["product_id"].split("-")
        market_key = self.exchange.name.lower() + buy_sym_id.upper() + sell_sym_id.upper()
        #TODO: remove if statement below
        if market_key not in self.last_update_ids.keys():
            self.last_update_ids[market_key] = 0
        timestamp = datetime.now()
        for order in update["changes"]:
            order[0] = "bid" if order[0] == "buy" else "ask"
            agg_orders.append(
                models.AggOrder(
                    timestamp=timestamp,
                    exchange_id=self.exchange.id,
                    order_type=order[0],
                    price=float(order[1]),
                    size=float(order[2]),
                    buy_sym_id=buy_sym_id,
                    sell_sym_id=sell_sym_id,
                    last_update_id=self.last_update_ids[market_key]
                )
            )
        if agg_orders:
            self.last_update_ids[market_key] += 1
        return [actions.InsertAction(agg_orders)]

    def _get_markets_uri(self):
        return (
            settings.COINBASE_API + "/" +
            settings.COINBASE_API_PRODUCTS
            )

    def _get_products_uri(self):
        return (
            settings.COINBASE_API + "/" +
            settings.COINBASE_API_PRODUCTS
        )

    async def get_markets(self):
        markets_uri = self._get_products_uri()
        async with aiohttp.ClientSession() as session:
            incomplete_markets = await self._fetch(session, markets_uri)
            incomplete_markets = self._parse_market(incomplete_markets)
            logging.debug("markets retrieved from %s: %s", self.exchange.name, incomplete_markets)
            markets = await self._get_volume(incomplete_markets)
            logging.debug("retrieved complete markets: %s", markets)
            actions = self._parse_markets(markets)
            self.on_event(actions)

    async def _get_volume(self, markets):
        complete_markets = []
        requests = 0
        async with aiohttp.ClientSession() as session:
            for market_id in markets:
                ticker_data = await self._fetch(session, settings.COINBASE_API+"/"+
                settings.COINBASE_API_PRODUCTS+"/"+market_id+
                "/"+settings.COINBASE_API_TICKER)
                complete_markets.append(self._parse_volume(ticker_data, market_id))
                requests = (requests + 1) % 3
                if requests == 0:
                    await asyncio.sleep(1)
            return complete_markets

    def _parse_markets(self, markets):
        new_markets = []
        exchange_markets = []
        coins = []
        for market in markets:
            coins.extend([
                models.Coin(symbol=market["buy_sym_id"]),
                models.Coin(symbol=market["sell_sym_id"]),
            ])
            pairs = sorted([market["buy_sym_id"], market["sell_sym_id"]])
            new_market = models.Market(
                first_coin_id=pairs[0],
                second_coin_id=pairs[1],
            )
            new_markets.append(new_market)
            exchange_markets.append(models.ExchangeMarket(
                quoted_volume=float(market["volume"]),
                quoted_volume_id=market["buy_sym_id"],
                exchange_id=self.exchange.id,
                first_coin_id=pairs[0],
                second_coin_id=pairs[1],
                quoted_vol_timestamp=market["timestamp"],
                original_name=market["market_id"]
            ))
        return [
            actions.InsertAction(coins),
            actions.InsertAction(new_markets),
            actions.InsertAction(exchange_markets),
        ]

    def _parse_volume(self, ticker, pair):
        return dict(
            buy_sym_id=pair.split("-")[0],
            sell_sym_id=pair.split("-")[1],
            volume=ticker["volume"],
            timestamp=ticker["time"],
            market_id=pair
        )

    def _parse_market(self, raw_markets):
        return [market["id"] for market in raw_markets]

    def _parse_match(self, match):
        # a trade occurred between two orders 
        return [actions.InsertAction([self._convert_raw_match(match)])]

    def _convert_raw_match(self, match):
        return models.Trade(
            timestamp=parse_date(match["time"]),
            exchange_id=self.exchange.id,
            trade_type=match["side"],
            buy_sym_id=match["product_id"].split("-")[0],
            sell_sym_id=match["product_id"].split("-")[1],
            maker_order_id=match["maker_order_id"],
            taker_order_id=match["taker_order_id"],
            price=float(match["price"]),
            size=float(match["size"]),
            exchange_trade_id=str(match["trade_id"])
        )

    def _get_events(self):
        return self._compute_events(self.event_type, settings.COINBASE_CHANNELS)

    async def _setup_connection(self, websocket):
        for market in self._all_markets:
            self._log_event(market, "connect", "trades")
            self._log_event(market, "connect", "agg_order_book")
        await self._send_message(websocket, "subscribe", self._all_markets, self._get_events())

    def _format_markets(self):
        self._all_markets = []
        for market in self.markets:
            self._all_markets.append('-'.join(market.split("_")))
            self._all_symbols.extend(market.split("_"))
    
    async def _send_message(self, websocket, request, product_ids, channels):
        data = dict(type=request, product_ids=product_ids, channels=channels)
        message = json.dumps(data)
        logging.debug("> %s: %s", request, product_ids)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)