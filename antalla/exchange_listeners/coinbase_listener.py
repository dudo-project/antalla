import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener

@ExchangeListener.register("coinbase")
class IdexListener(ExchangeListener):
    def __init__(self, exchange, on_event):
        super().__init__(exchange, on_event)
        self.running = False

    async def listen(self):
        self.running = True
        while self.running:
            try:
                await self._listen()
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError) as e:
                logging.error("coinbase websocket disconnected: %s", e)

    async def _listen(self):
        async with websockets.connect(settings.IDEX_WS_URL) as websocket: 
            #await self._setup_connection(websocket)
            while self.running:
                data = await websocket.recv()
                logging.debug("received %s from idex", data)
                #actions = self._parse_message(json.loads(data))
                #self.on_event(actions)


    