import asyncio
import json
import logging
import traceback

import sqlalchemy
import websockets

from . import db
from .exchange_listener import ExchangeListener


class WebsocketListener(ExchangeListener):
    def __init__(
        self, exchange, on_event, markets, ws_url, session=db.session, event_type=None
    ):
        super().__init__(
            exchange, on_event, markets, session=session, event_type=event_type
        )
        self._running = False
        self._ws_url = ws_url

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except sqlalchemy.exc.DBAPIError as e:
                self.session.rollback()
                logging.error("db error in db: %s", e)
                self._log_disconnection()
            except Exception as e:
                logging.error(
                    "error in %s: %s\n\t%s", self.exchange, e, traceback.format_exc()
                )
                self._log_disconnection()

    async def _listen(self):
        logging.debug("websocket connecting to: %s", self._ws_url)
        async with websockets.connect(self._ws_url) as websocket:
            await self._setup_connection(websocket)
            self._connected = True
            while self.running:
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                logging.debug("received %s from %s", data, self.exchange)
                actions = self._parse_message(json.loads(data))
                self.on_event(actions)

    async def _setup_connection(self, websocket):
        raise NotImplementedError()

    def _parse_message(self, message):
        raise NotImplementedError()

    def stop(self):
        self.running = False
        self._log_disconnection()
