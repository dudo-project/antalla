import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets
import aiohttp 

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener

# needs to be 5, 10, 20, 50, 100, 500 or 1000
DEPTH_SNAPSHOT_LIMIT = 1000

@ExchangeListener.register("binance")
class BinanceListener(ExchangeListener):
    def __init__(self, exchange, on_event):
        super().__init__(exchange, on_event)
        self.running = False
        self._get_ws_url()
        self._api_url = settings.BINANCE_API
        self._get_symbols()

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError) as e:
                logging.error("binance websocket disconnected: %s", e)

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

    def _parse_market(self, pair):
        # returns the individual coin symbols from a pair string of any possible length
        pairs = pair.split("_")
        if len(pairs) == 2:
            buy_sym_id = pairs[0]
            sell_sym_id = pairs[1]
        elif len(pairs[0]) == 6:
            buy_sym_id = pairs[0][0:3]
            sell_sym_id = pairs[0][3:6]
        elif len(pairs[0]) == 8:
            buy_sym_id = pairs[0][0:4]
            sell_sym_id = pairs[0][4:8]
        else:
            if all(sym in self._all_symbols for sym in [pairs[0][0:4], pairs[0][4:7]]):
                buy_sym_id = pairs[0][0:4]
                sell_sym_id = pairs[0][4:7]
            elif all(sym in self._all_symbols for sym in [pairs[0][0:3], pairs[0][3:7]]):
                buy_sym_id = pairs[0][0:3]
                sell_sym_id = pairs[0][3:7]
            else:
                raise Exception("unknown pair {} to parse. Check if both symbols are specified in settings.BINANCE_MARKETS".format(pairs[0]))
        return buy_sym_id, sell_sym_id

    def _parse_snapshot(self, snapshot, pair):
        pairs = self._parse_market(pair)
        order_info = models.AggOrder(
            #timestamp=,
            last_update_id=snapshot["lastUpdateId"],
            buy_sym_id=pairs[0],
            sell_sym_id=pairs[1],
            exchange=self.exchange,
        )
        orders = self._convert_raw_orders(snapshot, order_info, "bids", "asks")
        logging.debug("parsed %d orders in depth snapshot for pair '%s'", len(orders), pair.lower())
        return self._parse_agg_orders(orders)

    def _parse_depthUpdate(self, update):
        # FixMe: check for last "U" = "u+1" from previous update
        pair = self._parse_market(update["s"])
        order_info = models.AggOrder(
            timestamp=datetime.fromtimestamp(update["E"] / 1000),
            last_update_id=update["u"],
            buy_sym_id=pair[0],
            sell_sym_id=pair[1],
            exchange=self.exchange,
        )
        orders = self._convert_raw_orders(update, order_info, "b", "a")
        return self._parse_agg_orders(orders)

    def _convert_raw_orders(self, orders, order_info, bid_key, ask_key):
        all_orders = []
        for bid in orders[bid_key]:
            new_bid_order = models.AggOrder()
            new_bid_order = order_info
            new_bid_order.order_type = "bid"
            new_bid_order.price = bid[0]
            new_bid_order.quantity = bid[1]
            all_orders.append(new_bid_order)
        for ask in orders[ask_key]:
            new_ask_order = models.AggOrder()
            new_ask_order = order_info
            new_ask_order.order_type = "ask"
            new_ask_order.price = ask[0]
            new_ask_order.quantity = ask[1]
            all_orders.append(new_ask_order)        
        return all_orders

    def _parse_agg_orders(self, orders):
        return [actions.InsertAction(orders)]
        

    async def _fetch(self, session, url):
        async with session.get(url) as response:
            logging.debug("GET request: %s, status: %s", url, response.status)
            return await response.json()

    def stop(self):
        self.running = False

    def _parse_message(self, message):
        event, payload = message["data"]["e"], message["data"]
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_trade(self, trade):
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
            amount=float(raw_trade["q"]),
        )

        
         

        

