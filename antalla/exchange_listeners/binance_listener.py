import json
import logging

from datetime import datetime
import time

from dateutil.parser import parse as parse_date
import websockets
import aiohttp 

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

# needs to be 5, 10, 20, 50, 100, 500 or 1000
DEPTH_SNAPSHOT_LIMIT = 1000

@ExchangeListener.register("binance")
class BinanceListener(WebsocketListener):
    def __init__(self, exchange, on_event, ws_url=None):
        super().__init__(exchange, on_event, ws_url)
        self.running = False
        self._get_ws_url()
        self._api_url = settings.BINANCE_API
        self._get_symbols()

    async def _listen(self):
        async with websockets.connect(self._ws_url) as websocket: 
            initial_actions = await self._setup_snapshots()
            self.on_event(initial_actions)
            while self.running:
                data = await websocket.recv()
                logging.debug("received %s from binance", data)
                actions = self._parse_message(json.loads(data))
                self.on_event(actions)

    def _get_symbols(self):
        self._all_symbols = []
        for pair in settings.BINANCE_MARKETS:
            self._all_symbols.extend(self._parse_market(pair))

    def _get_ws_url(self):
        self._ws_url = settings.BINANCE_COMBINED_STREAM
        for stream in settings.BINANCE_STREAMS:
            for pair in settings.BINANCE_MARKETS:
                self._ws_url = self._ws_url + ''.join(pair.lower().split("_")) + "@" + stream + "/"
        logging.debug("websocket connecting to: %s", self._ws_url)

    async def _setup_snapshots(self):
        actions = []
        for pair in settings.BINANCE_MARKETS:
            async with aiohttp.ClientSession() as session:
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
        pair = self._parse_market(update["s"])
        logging.debug("parsed %d orders in 'depth update' for pair '%s'", len(orders), ''.join(pair))
        return self._parse_agg_orders(orders)

    def _get_markets_uri(self):
        return (
            settings.BINANCE_API + "/" +
            settings.BINANCE_PUBLIC_API + "/" +
            settings.BINANCE_API_MARKETS
        )

    def _create_agg_order(self, order_info):
        pair = self._parse_market(order_info["pair"])
        return models.AggOrder(
            timestamp=datetime.fromtimestamp(order_info["timestamp"] / 1000),
            last_update_id=order_info["last_update_id"],
            buy_sym_id=pair[0],
            sell_sym_id=pair[1],
            exchange = self.exchange,  
        )

    def _convert_raw_orders(self, orders, bid_key, ask_key, order_info):
        all_orders = []
        for bid in orders[bid_key]:
            new_bid_order = self._create_agg_order(order_info)
            new_bid_order.order_type = "bid"
            new_bid_order.price = float(bid[0])
            new_bid_order.size = float(bid[1])
            all_orders.append(new_bid_order)
        for ask in orders[ask_key]:
            new_ask_order = self._create_agg_order(order_info)
            new_ask_order.order_type = "ask"
            new_ask_order.price = float(ask[0])
            new_ask_order.size = float(ask[1])
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
        trade_symbols = self._parse_market(trade["s"])
        trade = self._convert_raw_trade(trade, trade_symbols[0], trade_symbols[1])
        return [actions.InsertAction([trade])] 
        
    def _convert_raw_trade(self, raw_trade, buy_sym, sell_sym):
        return models.Trade(
            timestamp=datetime.fromtimestamp(raw_trade["T"] / 1000),
            exchange=self.exchange,
            buy_sym_id=buy_sym,
            sell_sym_id=sell_sym,
            maker=raw_trade["b"],
            taker=raw_trade["a"],
            price=float(raw_trade["p"]),
            size=float(raw_trade["q"]),
        )

    def _parse_market(self, pair):
        """
        returns the individual coin symbols from a pair string of any possible length

        >>> from types import SimpleNamespace
        >>> symbols = ["BTC", "ETH", "WAVE", "USD"]
        >>> dummy_self = SimpleNamespace(_all_symbols=symbols)
        >>> BinanceListener._parse_market(dummy_self, "BTC_ETH")
        ('BTC', 'ETH')
        >>> BinanceListener._parse_market(dummy_self, "BTCETH")
        ('BTC', 'ETH')
        >>> BinanceListener._parse_market(dummy_self, "WAVEETH")
        ('WAVE', 'ETH')
        >>> BinanceListener._parse_market(dummy_self, "USDWAVE")
        ('USD', 'WAVE')
        """   
        split_at = lambda string, n: (string[:n], string[n:])
        symbols = pair.split("_")
        if len(symbols) == 2:
            return tuple(symbols)
        if len(pair) % 2 == 0:
            return split_at(pair, len(pair) // 2)
        for split_index in [3, 4]:
            symbols = split_at(pair, split_index)
            if all(sym in self._all_symbols for sym in symbols):
                return symbols
        raise Exception("unknown pair {} to parse. Check if both symbols are specified in settings.BINANCE_MARKETS".format(pair))


    def _parse_markets(self, markets):
        new_markets = []
        exchange_markets = []
        for market in markets:
            pair = self._parse_market(market["symbol"])
            if len(pair) == 2:
                new_market = models.Market(
                    buy_sym_id=pair[0],
                    sell_sym_id=pair[1]
                )
                new_markets.append(new_market)
                exchange_markets.append(models.ExchangeMarket(
                    volume=float(market["volume"]),
                    exchange=self.exchange,
                    market=new_market
                ))
            else:
                logging.debug("parse markets for '{}' - invalid market format: '{}' is not a pair of markets - IGNORE".format(self.exchange.name, market))  
        return [actions.InsertAction(new_markets), actions.InsertAction(exchange_markets)]
        