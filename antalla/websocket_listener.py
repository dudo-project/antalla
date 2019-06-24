
import websockets
import json
import logging
import asyncio

from .exchange_listener import ExchangeListener

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
            except (websockets.exceptions.InvalidState,
                    websockets.exceptions.InvalidHandshake,
                    ConnectionResetError) as e:
                logging.error("%s websocket disconnected: %s", self.exchange, e)

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
