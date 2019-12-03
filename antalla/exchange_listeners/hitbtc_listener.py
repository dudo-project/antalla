import json
import logging

from datetime import datetime
from os import path

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

TRADES_LIMIT = 1000

@ExchangeListener.register("hitbtc")
class HitBTCListener(WebsocketListener):
    def __init__(self,
                 exchange,
                 on_event,
                 markets=settings.HITBTC_MARKETS,
                 ws_url=settings.HITBTC_WS_URL,
                 session=db.session,
                 event_type=None):
        super().__init__(exchange, on_event, markets, ws_url, session=session, event_type=event_type)
        self._all_symbols = []

    def _get_uri(self, endpoint):
        return path.join(settings.HITBTC_API, endpoint)
        
    async def fetch_all_symbols(self, session):
        exchange_info = await self._fetch(session, self._get_uri(settings.HITBTC_API_SYMBOLS))
        all_symbols = []
        logging.debug("hitbtc - markets retrieved - %s", exchange_info)
        for symbol_info in exchange_info:
            all_symbols.append(dict(
                id=symbol_info["id"],
                baseCurrency=symbol_info["baseCurrency"],
                quoteCurrency=symbol_info["quoteCurrency"]
                ))
        return all_symbols

    async def get_markets(self):
        async with aiohttp.ClientSession() as session:
            symbols = await self.fetch_all_symbols(session)
            self._all_symbols = symbols
            markets_uri = self._get_uri(settings.HITBTC_API_MARKETS)
            logging.debug("hitbtc - markets uri - %s", markets_uri)
            markets = await self._fetch(session, markets_uri)
            logging.debug("hitbtc - markets retrieved: %s", markets)
            actions = self._parse_markets(markets)
            self.on_event(actions)

    def _parse_market_to_symbols(self, market, all_symbols):
        for m in all_symbols:
            if m["id"] == market.upper():
                base, quote = m["baseCurrency"], m["quoteCurrency"]
                # edge case with USDTUSD pair
                if base == "USD" and market.startswith("USDT") and quote != "TUSD":
                    base = "USDT"
                if quote == "USD" and market.endswith("USDT"):
                    quote = "USDT"
                return base, quote
        return None, None

    def _parse_markets(self, markets):
        add_markets = []
        add_exchange_markets = []
        add_coins = []
        for market in markets:
            pair = self._parse_market_to_symbols(market["symbol"], self._all_symbols)
            if pair is not None:
                pair = list(pair)
                add_coins.extend([
                    models.Coin(symbol=pair[0]),
                    models.Coin(symbol=pair[1]),
                ])
                quoted_volume_id = pair[0]
                pair.sort()
                new_market = models.Market(
                    first_coin_id=pair[0],
                    second_coin_id=pair[1]
                )
                add_markets.append(new_market)
                add_exchange_markets.append(models.ExchangeMarket(
                    quoted_volume=float(market["volume"]),
                    quoted_volume_id=quoted_volume_id,
                    exchange_id=self.exchange.id,
                    first_coin_id=pair[0],
                    second_coin_id=pair[1],
                    quoted_vol_timestamp=parse_date(market["timestamp"]),
                    original_name=market["symbol"]
                ))
            else:
                logging.warning("symbol not found in fetched symbols: %s", market["symbol"])
        return [ 
            actions.InsertAction(add_coins),
            actions.InsertAction(add_markets),
            actions.InsertAction(add_exchange_markets)
            ]

    def _parse_message(self, message):
        if "method" in message.keys():
            event, payload = message["method"], message["params"]
            func = getattr(self, f"_parse_{event}", None)
            if func:
                return func(payload)
            return []
        else:
            logging.warning("unknown message received < '{}'".format(message))
            return []

    def _parse_snapshotOrderbook(self, snapshot):
        logging.debug("snapshot ob: %s", snapshot)
        return self._handle_raw_orders(snapshot)

    def _handle_raw_orders(self, raw_orders):
        market = self._parse_market_to_symbols(raw_orders["symbol"], self._all_symbols)
        if market is not None:
            order_info = {
                "pair": market[0].upper() + market[1].upper(),
                "timestamp": raw_orders["timestamp"],
                "last_update_id": raw_orders["sequence"],              
            }
            orders = self._convert_raw_orders(raw_orders, "bid", "ask", order_info, raw_orders["sequence"])
            logging.debug("parsed %d orders in depth snapshot for pair '%s'", len(orders), raw_orders["symbol"])
            return self._parse_agg_orders(orders)
        else:
            logging.warning("unable to parse market '%s' to two symbols", raw_orders["symbol"])
            return []

    def _create_agg_order(self, order_info, order_type, price, size):
        pair = self._parse_market_to_symbols(order_info["pair"], self._all_symbols)
        if pair is not None:
            return models.AggOrder(
                timestamp=parse_date(order_info["timestamp"]),
                last_update_id=order_info["last_update_id"],
                buy_sym_id=pair[0],
                sell_sym_id=pair[1],
                exchange_id=self.exchange.id,
                order_type=order_type,
                price=price,
                size=size 
            )
        else:
            logging.warning("no market found for: '%s'", order_info["pair"])

    def _parse_updateOrderbook(self, orders):
        return self._handle_raw_orders(orders)

    def _convert_raw_orders(self, orders, bid_key, ask_key, order_info, sequence):
        all_orders = []
        for bid in orders[bid_key]:
            new_bid_order = self._create_agg_order(
                order_info, "bid", float(bid["price"]), float(bid["size"]))
            if new_bid_order is not None:
                all_orders.append(new_bid_order)
        for ask in orders[ask_key]:
            new_ask_order = self._create_agg_order(
                order_info, "ask", float(ask["price"]), float(ask["size"]))
            if new_ask_order is not None:
                all_orders.append(new_ask_order)       
        return all_orders

    def _parse_agg_orders(self, orders):
        return [actions.InsertAction(orders)]

    async def _setup_connection(self, websocket):
        async with aiohttp.ClientSession() as session:
            self._all_symbols = await self.fetch_all_symbols(session)           
        for market in self.markets:
            logging.info("market: %s", market)
            if self.event_type is None or self.event_type == "depth":
                orderbook_message = await self._subscribe_orderbook(market, websocket)
                self._log_event(market, "connect", "agg_order_book")
                self._parse_message(orderbook_message)
            if self.event_type is None or self.event_type == "trade":
                trades_message = await self._subscribe_trades(market, websocket)
                self._log_event(market, "connect", "trades")
                self._parse_message(trades_message)

    async def _send_suscribe_message(self, method, params, websocket):
        message = dict(method=method, id=settings.HITBTC_API_KEY)
        message["params"] = params
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)
    
    async def _subscribe_orderbook(self, market, websocket):
        params = {"symbol": market.upper()}
        return await self._send_suscribe_message("subscribeOrderbook", params, websocket) 
        
    async def _subscribe_trades(self, market, websocket):
        params = {"symbol": market.upper(), "limit": TRADES_LIMIT}
        return await self._send_suscribe_message("subscribeTrades", params, websocket)

    def _parse_updateTrades(self, trades):
        return self._parse_raw_trades(trades)

    def _parse_raw_trades(self, snapshot):
        market = self._parse_market_to_symbols(snapshot["symbol"], self._all_symbols)
        trades = []
        for trade in snapshot["data"]:
            trades.append(models.Trade(
                timestamp=parse_date(trade["timestamp"]),
                trade_type=trade["side"],
                exchange_id=self.exchange.id,
                buy_sym_id= market[0],
                sell_sym_id= market[1],
                price=float(trade["price"]),
                size=float(trade["quantity"]),
                exchange_trade_id=trade["id"]
            ))
        return [actions.InsertAction(trades)]
