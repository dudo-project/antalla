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

@ExchangeListener.register("coinbase")
class CoinbaseListener(ExchangeListener):
    def __init__(self, exchange, on_event):
        super().__init__(exchange, on_event)
        self.running = False
        self._format_markets()

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError) as e:
                logging.error("coinbase websocket disconnected: %s", e)

    async def _listen(self):
        async with websockets.connect(settings.COINBASE_WS_URL) as websocket: 
            # TODO: get snapshot of orderbook via GET
            await self._setup_connection(websocket)
            while self.running:
                data = await websocket.recv()
                # FIXME: implement error handling for case of 'data["type"] == "error"'
                logging.debug("received %s from coinbase", data)
                actions = self._parse_message(json.loads(data))
                self.on_event(actions)
    
    def _parse_message(self, message):
        event, payload = message["type"], message
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_received(self, received):
        return [actions.InsertAction([self._convert_raw_order(received)])]

    def _convert_raw_order(self, received):
        order = models.Order(
            timestamp=parse_date(received["time"]),
            buy_sym_id=received["product_id"].split("-")[0],
            sell_sym_id=received["product_id"].split("-")[1],
            exchange_order_id=received["order_id"],
            exchange=self.exchange,
            side=received["side"],
            order_type=received["order_type"]
        )
        if "funds" in received:
            order.funds = received["funds"]
        else:
            order.price = received["price"]
            order.quantity = received["size"]
        return order

    def _parse_open(self, open_order):
        # only for orders that are not fully filled immediately 
        return [actions.InsertAction([self._convert_raw_open_order(open_order)])]

    def _convert_raw_open_order(self, open_order):
        return models.Order(
            timestamp=parse_date(open_order["time"]),
            buy_sym_id=open_order["product_id"].split("-")[0],
            sell_sym_id=open_order["product_id"].split("-")[1],
            exchange_order_id=open_order["order_id"],
            side=open_order["side"],
            price=open_order["price"],
            remaining_size=open_order["remaining_size"],
            exchange=self.exchange
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

    def _parse_change(self, update):
        # an order has changed: result of self-trade prevention adjusting order size or available funds
        update_fields = {}
        update_fields["last_updated"]
        if "new_size" in update:
            update_fields["new_size"] = update["new_size"]
        elif "new_funds" in update:
            update_fields["new_funds"] = update["new_funds"]
        else:
            # FIXME: raise an exception
            logging.debug("failed to process order: %s", update)
        return [actions.UpdateAction(
            models.Order, 
            {"exchange_order_id": update["order_id"], "exchange_id": self.exchange.id},
            update_fields
            )]

    def _parse_match(self, match):
        # a trade occurred between two orders 
        return [actions.InsertAction([self._convert_raw_match(match)])]

    def _convert_raw_match(self, match):
        return models.Trade(
            timestamp=parse_date(match["time"]),
            exchange=self.exchange,
            trade_type=match["side"],
            buy_sym_id=match["product_id"].split("-")[0],
            sell_sym_id=match["product_id"].split("-")[1],
            maker_order_id=match["maker_order_id"],
            taker_order_id=match["taker_order_id"],
            price=match["price"],
            amount=match["size"]
        )

    async def _setup_connection(self, websocket):
        await self._send_message(websocket, "subscribe", self._all_markets, settings.COINBASE_CHANNELS)         

    def _format_markets(self):
        self._all_markets = []
        for market in settings.COINBASE_MARKETS:
            self._all_markets.append('-'.join(market.split("_")))
    
    async def _send_message(self, websocket, request, product_ids, channels):
        data = dict(type=request, product_ids=product_ids, channels=channels)
        message = json.dumps(data)
        print(message)
        logging.debug("> %s: %s", request, product_ids)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)

    def stop(self):
        self.running = False

