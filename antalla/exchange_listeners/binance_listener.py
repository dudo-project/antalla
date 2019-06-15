import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets
import requests
import asyncio

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
        self._socket_managers

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError) as e:
                logging.error("binance websocket disconnected: %s", e)

    async def _listen(self):
        for pair in settings.BINANCE_MARKETS:
            for stream in settings.BINANCE_STREAMS:
                bsm = BinanceSocketManager(pair, stream, self.exchange)
                self._socket_managers.append(bsm)
        await asyncio.gather(*[bsm.setup_connection()] for bsm in self._socket_managers])
        #actions = self._parse_message(json.loads(data))
        #self.on_event(actions)


    def stop(self):
        self.running = False
        for socket_manager in self._socket_managers:
            socket_manager.stop()


class BinanceSocketManager():
    def __init__(self, pair, stream, exchange, on_event):
        self._ws_url = settings.BINANCE_SINGLE_STREAM
        self._pair = pair.lower()
        self._stream = stream.lower()
        self._exchange = exchange

    def _get_depth_snapshot(self):
        PARAMS = {"symbol": self._pair.upper(), "limit": DEPTH_SNAPSHOT_LIMIT}
        snapshot = requests.get(url=settings.BINANCE_API, params=PARAMS)
        logging.debug("depth snapshot for '%s': %s", self._pair, snapshot.json())
        return snapshot.json()

    def stop(self):
        self.running = False

    async def setup_connection(self):
        self.running = True
        ws_url = self._ws_url+self._pair+"@"+self._stream
        logging.debug("connecting to websocket url: %s", ws_url)
        async with websockets.connect(ws_url) as websocket:
            self._set_up_orderbook()
            while self.running:
                data = await websocket.recv()
                logging.debug("received %s from binance", data)
                actions = self._parse_message(json.loads(data))
                self.on_event(actions)

    def _set_up_orderbook(self):
        snapshot = self._get_depth_snapshot()
        logging.debug("retrieve order book depth snapshot: %s", snapshot)
    
    def _parse_message(self, message):
        event, payload = message["e"], json.loads(message)
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_trade(self, trade):
        trade = self._convert_raw_trade(trade, trade["s"][0:3], trade["s"][3:6])
        # FixMe: update filled orders
        return actions.InsertAction(trade)

    def _convert_raw_trade(self, raw_trade, buy_sym, sell_sym):
        return models.Trade(
            timestamp=datetime.fromtimestamp(raw_trade["T"]),
            exchange=self._exchange,
            buy_sym_id=buy_sym,
            sell_sym_id=sell_sym,
            maker=raw_trade["b"],
            taker=raw_trade["a"],
            price=float(raw_trade["p"]),
            amount=float(raw_trade["q"]),
        )

    def _parse_depthUpdate(self, update):
        # FixMe: check for last "U" = "u+1" from previous update
        # check if bid/ask update exists in DB
        # if quantity == 0 then remove
        orders = []

        agg_order = models.AggOrder(
            timestamp=datetime.fromtimestamp(update["e"]),
            last_update_id=update["u"]
            buy_sym_id=update["s"][0:3],
            sell_sym_id=update["s"][3:6],
            exchange=self.exchange,
        )

        for bid in update["b"]:
            new_bid_order = agg_order
            new_bid_order.order_type = "bid"
            new_bid_order.price = bid[0]
            new_bid_order.quantity = bid[1]
            orders.append(new_bid_order)

        for ask in update["a"]:
            new_ask_order = agg_order
            new_ask_order.order_type = "ask"
            new_ask_order.price = ask[0]
            new_ask_order.quantity = ask[1]
            orders.append(new_ask_order)

        # check if order type with price level exists
        
         

        

