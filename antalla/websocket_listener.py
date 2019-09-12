
import websockets
import json
import logging
import asyncio
import sqlalchemy

from .exchange_listener import ExchangeListener
from .db import session

class WebsocketListener(ExchangeListener):
    def __init__(self, exchange, on_event, markets, ws_url):
        super().__init__(exchange, on_event, markets)
        self._running = False
        self._ws_url = ws_url

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except sqlalchemy.exc.DBAPIError as e:
                session.rollback()
                logging.error("db error in %s: %s", e)
                self._log_disconnection()
            except Exception as e:
                logging.error("error in %s: %s", self.exchange, e)
                self._log_disconnection()

    async def _listen(self):
        async with websockets.connect(self._ws_url) as websocket: 
            await self._setup_connection(websocket)
            while self.running:
                data = await websocket.recv()
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