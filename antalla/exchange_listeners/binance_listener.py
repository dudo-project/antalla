#%%x
from os import path
import json
import logging

from datetime import datetime
import time

from dateutil.parser import parse as parse_date
import websockets
import aiohttp
import asyncio 

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

# needs to be 5, 10, 20, 50, 100, 500 or 1000
DEPTH_SNAPSHOT_LIMIT = 1000

@ExchangeListener.register("binance")
class BinanceListener(WebsocketListener):
    def __init__(self, exchange, on_event, markets=settings.BINANCE_MARKETS, ws_url=None):
        super().__init__(exchange, on_event, markets, ws_url)
        self.running = False
        self._get_ws_url()
        self._api_url = settings.BINANCE_API
        self._all_symbols = []

    async def _listen(self):
        initial_actions = await self._setup_listener()
        self.on_event(initial_actions)
        await super()._listen()

    def _get_ws_url(self):
        self._ws_url = settings.BINANCE_COMBINED_STREAM
        for stream in settings.BINANCE_STREAMS:
            for pair in self.markets:
                self._ws_url = self._ws_url + ''.join(pair.lower().split("_")) + "@" + stream + "/"
        logging.debug("websocket connecting to: %s", self._ws_url)

    async def _setup_connection(self, websocket):
        for stream in settings.BINANCE_STREAMS:
            for pair in self.markets:
                collected_data = self._get_event_data_collected(stream)
                self._log_event(pair, "connect", collected_data)
                

    def _get_event_data_collected(self, data_type):
        if data_type == "trade":
            return "trades"
        elif data_type == "depth":
            return "agg_order_book"
        else:
            logging.debug("unknown event type for 'data collected' - {}".format(data_type))
            return "Unknown"

    async def _setup_listener(self):
        actions = []
        async with aiohttp.ClientSession() as session:
            self._all_symbols = await self.fetch_all_symbols(session)
            for pair in self.markets:
                uri = settings.BINANCE_API + "/api/v1/depth?symbol=" + ''.join(pair.upper().split("_")) + "&limit=" + str(DEPTH_SNAPSHOT_LIMIT)
                snapshot = await self._fetch(session, uri)
                logging.debug("GET orderbook snapshot for '%s': %s", pair, snapshot)
                actions.extend(self._parse_snapshot(snapshot, pair))
        return actions

    def _parse_snapshot(self, snapshot, pair):
        order_info = {
            "pair": pair,
            "timestamp": time.time(),
            "last_update_id": snapshot["lastUpdateId"],              
        }
        orders = self._convert_raw_orders(snapshot, "bids", "asks", order_info)
        logging.debug("parsed %d orders in depth snapshot for pair '%s'", len(orders), pair.lower())
        return self._parse_agg_orders(orders)

    def _parse_depthUpdate(self, update):
        # FIXME: could check for last "U" = "u+1" from previous update
        order_info = {
            "pair": update["s"],
            "timestamp": update["E"],
            "last_update_id": update["u"],
        }
        orders = self._convert_raw_orders(update, "b", "a", order_info)
        pair = self._parse_market_to_symbols(update["s"], self._all_symbols)
        logging.debug("parsed %d orders in 'depth update' for pair '%s'", len(orders), ''.join(pair))
        return self._parse_agg_orders(orders)

    def _get_uri(self, endpoint):
        return path.join(settings.BINANCE_API, settings.BINANCE_PUBLIC_API, endpoint)

    def _create_agg_order(self, order_info, order_type, price, size):
        pair = self._parse_market_to_symbols(order_info["pair"], self._all_symbols)
        return models.AggOrder(
            timestamp=datetime.fromtimestamp(order_info["timestamp"] / 1000),
            last_update_id=order_info["last_update_id"],
            buy_sym_id=pair[0],
            sell_sym_id=pair[1],
            exchange_id=self.exchange.id, 
            order_type=order_type,
            price=price,
            size=size,
        )

    def _convert_raw_orders(self, orders, bid_key, ask_key, order_info):
        all_orders = []
        for bid in orders[bid_key]:
            new_bid_order = self._create_agg_order(
                order_info, "bid", float(bid[0]), float(bid[1]))
            all_orders.append(new_bid_order)
        for ask in orders[ask_key]:
            new_ask_order = self._create_agg_order(
                order_info, "ask", float(ask[0]), float(ask[1]))
            all_orders.append(new_ask_order)       
        return all_orders

    def _parse_agg_orders(self, orders):
        return [actions.InsertAction(orders)]

    def _parse_message(self, message):
        event, payload = message["data"]["e"], message["data"]
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_trade(self, trade):
        # 'trade["s"]' = e.g. "BNBBTC"
        trade_symbols = self._parse_market_to_symbols(trade["s"], self._all_symbols)
        trade = self._convert_raw_trade(trade, trade_symbols[0], trade_symbols[1])
        return [actions.InsertAction([trade])] 
        
    def _convert_raw_trade(self, raw_trade, buy_sym, sell_sym):
        return models.Trade(
            timestamp=datetime.fromtimestamp(raw_trade["T"] / 1000),
            exchange_id=self.exchange.id,
            buy_sym_id=buy_sym,
            sell_sym_id=sell_sym,
            maker=raw_trade["b"],
            taker=raw_trade["a"],
            price=float(raw_trade["p"]),
            size=float(raw_trade["q"]),
            exchange_trade_id=str(raw_trade["t"])
        )

    async def fetch_all_symbols(self, session):
        exchange_info = await self._fetch(session, self._get_uri(settings.BINANCE_API_INFO))
        all_symbols = set()
        for symbol_info in exchange_info["symbols"]:
            all_symbols.add(symbol_info["baseAsset"])
            all_symbols.add(symbol_info["quoteAsset"])
        return set(all_symbols)

    async def get_markets(self):
        async with aiohttp.ClientSession() as session:
            symbols = await self.fetch_all_symbols(session)
            self._all_symbols = symbols
            markets = await self._fetch(session, self._get_uri(settings.BINANCE_API_MARKETS))
            logging.debug("markets retrieved from %s: %s", self.exchange.name, markets)
            actions = self._parse_markets(markets)
            self.on_event(actions)

    def _parse_markets(self, markets):
        new_markets = []
        exchange_markets = []
        coins = []
        for market in markets:
            pair = self._parse_market_to_symbols(market["symbol"], self._all_symbols)
            if len(pair) == 2:
                coins.extend([
                    models.Coin(symbol=pair[0]),
                    models.Coin(symbol=pair[1]),
                ])
                pair = list(pair)
                quoted_volume_id = pair[0]
                pair.sort()
                new_market = models.Market(
                    first_coin_id=pair[0],
                    second_coin_id=pair[1]
                )
                new_markets.append(new_market)
                exchange_markets.append(models.ExchangeMarket(
                    quoted_volume=float(market["volume"]),
                    quoted_volume_id=quoted_volume_id,
                    exchange_id=self.exchange.id,
                    first_coin_id=pair[0],
                    second_coin_id=pair[1],
                    quoted_vol_timestamp=datetime.fromtimestamp(time.time()),
                    original_name=market["symbol"]
                ))
            else:
                logging.debug("parse markets for '{}' - invalid market format: '{}' is not a pair of markets - IGNORE".format(self.exchange.name, market))  
        return [
            actions.InsertAction(coins),
            actions.InsertAction(new_markets),
            actions.InsertAction(exchange_markets)
        ]
