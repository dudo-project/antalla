import json
import logging
from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener


@ExchangeListener.register("idex")
class IdexListener(ExchangeListener):
    def __init__(self, exchange, on_event):
        super().__init__(exchange, on_event)
        self.running = False

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except websockets.exceptions.ConnectionClosed as e:
                logging.error("idex websocket disconnected: %s", e)

    async def _listen(self):
        async with websockets.connect(settings.IDEX_WS_URL) as websocket: 
            await self._setup_connection(websocket)
            while self.running:
                data = await websocket.recv()
                logging.debug("received %s from idex", data)
                actions = self._parse_message(json.loads(data))
                self.on_event(actions)

    def stop(self):
        self.running = False

    async def _send_message(self, websocket, request, payload, **kwargs):
        data = dict(request=request, payload=json.dumps(payload))
        data.update(kwargs)
        message = json.dumps(data)
        logging.debug("> %s: %s", request, payload)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)

    async def _setup_connection(self, websocket):
        handshake_data = dict(version="1.0.0", key=settings.IDEX_API_KEY)
        handshake_res = await self._send_message(websocket, "handshake", handshake_data)

        subscription_data = dict(topics=settings.MARKETS, events=settings.IDEX_EVENTS)
        await self._send_message(websocket, "subscribeToMarkets",
                                 subscription_data, sid=handshake_res["sid"])

    def _parse_message(self, message):
        event, payload = message["event"], json.loads(message["payload"])
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_market_orders(self, payload):
        buy_sym, sell_sym = payload["market"].split("_")
        orders = [self._convert_raw_order(order, buy_sym, sell_sym)
                  for order in payload["orders"]]
        return [actions.InsertAction(orders)]

    def _convert_raw_order(self, raw_order, buy_sym, sell_sym):
        return models.Order(
            timestamp=parse_date(raw_order["createdAt"]),
            exchange=self.exchange,
            buy_sym_id=buy_sym,
            sell_sym_id=sell_sym,
            amount_buy=float(raw_order["amountBuy"]),
            amount_sell=float(raw_order["amountSell"]),
            user=raw_order["user"],
            exchange_order_id=raw_order["hash"],
        )

    def _parse_market_cancels(self, payload):
        update_actions = []
        for cancel in payload["cancels"]:
                update_actions.append(actions.UpdateAction(
                    models.Order,
                    {"exchange_order_id": cancel["orderHash"]},
                    ("cancelled_at", parse_date(cancel["createdAt"]))
                ))
        return update_actions


        