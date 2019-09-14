import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets
import aiohttp
import asyncio

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

@ExchangeListener.register("coinbase")
class CoinbaseListener(WebsocketListener):
    def __init__(self, exchange, on_event, markets=settings.COINBASE_MARKETS, ws_url=settings.COINBASE_WS_URL):
        super().__init__(exchange, on_event, markets, ws_url)
        self._format_markets()
        self.running = False

    def _parse_message(self, message):
        event, payload = message["type"], message
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []
    
    def _parse_received(self, received):
        order, funds, size = self._convert_raw_order(received)
        inserts = [actions.InsertAction([order])]
        if funds:
            inserts.append(actions.InsertAction([funds]))
        if size:
            inserts.append(actions.InsertAction([size]))
        return inserts

    def _parse_snapshot(self, snapshot):
        agg_orders = []
        buy_sym_id, sell_sym_id = update["product_id"].split("-")
        timestamp = datetime.now()
        order_info = dict(
            timestamp=timestamp,
            exchange_id=self.exchange.id,
            buy_sym_id=buy_sym_id,
            sell_sym_id=sell_sym_id
        )
        bids = self._create_orders("bid", order_info, snapshot["bids"])
        asks = self._create_orders("ask", order_info, snapshot["asks"])
        agg_orders.extend(bids)
        agg_orders.extend(asks)
        logging.debug(" {} - aggregated order book snapshot -  agg orders: {}".format(self.exchange.name, len(agg_orders)))
        return actions.InsertAction(agg_orders)

    def _create_orders(self, order_type, order_info, orders):
        orders = []
        for order in orders:
            orders.append(models.AggOrder(
                timestamp=order_info["timestamp"],
                exchange_id=self.exchange.id,
                order_type=order_type,
                price=float(order[0]),
                size=float(order[1]),
                buy_sym_id=order_info["buy_sym_id"],
                sell_sym_id=order_info["sell_sym_id"]
            ))        
        return orders

    # TODO: add check for valid market
    def _parse_l2update(self, update):
        agg_orders = []
        buy_sym_id, sell_sym_id = update["product_id"].split("-")
        timestamp = datetime.now()
        for order in update["changes"]:
            order[0] = "bid" if order[0] == "buy" else "ask"
            #logging.warning("{} - invalid order length to process".format(self.exchange.name)) if len(order) != 3
            agg_orders.append(
                models.AggOrder(
                    timestamp=timestamp,
                    exchange_id=self.exchange.id,
                    order_type=order[0],
                    price=float(order[1]),
                    size=float(order[2]),
                    buy_sym_id=buy_sym_id,
                    sell_sym_id=sell_sym_id
                )
            )
        logging.debug(" {} - aggregated order book update - agg orders: {}".format(self.exchange.name, len(agg_orders)))
        return actions.InsertAction(agg_orders)



    def _create_agg_orders(self, all_orders):



    def _convert_raw_order(self, received):
        order = models.Order(
            timestamp=parse_date(received["time"]),
            buy_sym_id=received["product_id"].split("-")[0],
            sell_sym_id=received["product_id"].split("-")[1],
            exchange_order_id=received["order_id"],
            exchange_id=self.exchange.id,
            side=received["side"],
            order_type=received["order_type"]
        )
        if "funds" in received:
            funds = self._new_market_order_funds(
                received["time"], 
                received["funds"],
                received["order_id"]
            )
            return order, funds, None
        else:
            order.price = float(received["price"])
            size = self._new_order_size(
                received["time"],
                received["size"],
                received["order_id"]
            )
            return order, None, size

    def _parse_open(self, open_order):
        # only for orders that are not fully filled immediately 
        order_size = self._new_order_size(
                open_order["time"],
                open_order["remaining_size"],
                open_order["order_id"]
            )
        return [
            actions.InsertAction([self._convert_raw_open_order(open_order)]),
            actions.InsertAction([order_size])
        ]

    def _convert_raw_open_order(self, open_order):
        return models.Order(
            timestamp=parse_date(open_order["time"]),
            buy_sym_id=open_order["product_id"].split("-")[0],
            sell_sym_id=open_order["product_id"].split("-")[1],
            exchange_order_id=open_order["order_id"],
            side=open_order["side"],
            price=float(open_order["price"]),
            exchange_id=self.exchange.id,
        )
        
    def _parse_done(self, order):
        # order is no longer on the order book; message sent for fully filled or cancelled orders
        # market orders will not have remaining_size or price field as they are never in order book
        update_fields = {}
        update_fields["remaining_size"] = order["remaining_size"]
        if order["reason"] == "filled":
            update_fields["filled_at"] = parse_date(order["time"])
        elif order["reason"] == "canceled":
            update_fields["cancelled_at"] = parse_date(order["time"])
        else:
            logging.error("failed to process order: %s", order)
        return [actions.UpdateAction(
            models.Order, 
            {"exchange_order_id": order["order_id"], "exchange_id": self.exchange.id},
            update_fields
            )] 

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

    def _new_order_size(self, timestamp, size, order_id):
        return models.OrderSize(
            timestamp=parse_date(timestamp),
            exchange_id=self.exchange.id,
            exchange_order_id=order_id,
            size=float(size)
        )

    def _new_market_order_funds(self, timestamp, funds, order_id):
        return models.MarketOrderFunds(
            timestamp=parse_date(timestamp),
            exchange_id=self.exchange.id,
            exchange_order_id=order_id,
            funds=float(funds)
        )

    def _parse_change(self, update):
        # an order has changed: result of self-trade prevention adjusting order size or available funds
        if "new_size" in update:
            return [actions.InsertAction([self._new_order_size(
                update["time"],
                update["new_size"],
                update["order_id"]
            )])]
        elif "new_funds" in update:
            return [actions.InsertAction([self._new_market_order_funds(
                update["time"],
                update["new_funds"],
                update["order_id"]
            )])]
        else:
            # FIXME: raise an exception
            logging.debug("failed to process order: %s", update)
        return []

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

    async def _setup_connection(self, websocket):
        await self._send_message(websocket, "subscribe", self._all_markets, settings.COINBASE_CHANNELS)         

    def _format_markets(self):
        self._all_markets = []
        for market in self.markets:
            self._all_markets.append('-'.join(market.split("_")))
    
    async def _send_message(self, websocket, request, product_ids, channels):
        data = dict(type=request, product_ids=product_ids, channels=channels)
        message = json.dumps(data)
        logging.debug("> %s: %s", request, product_ids)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)