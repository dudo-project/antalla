import aiohttp
import json
import logging
from .base_factory import BaseFactory

class ExchangeListener(BaseFactory):
    def __init__(self, exchange, on_event):
        self.exchange = exchange
        self.on_event = on_event

    async def listen(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    async def get_markets(self):
        markets_uri = self._get_markets_uri()
        async with aiohttp.ClientSession() as session:
            markets = await self._fetch(session, markets_uri)
            logging.debug("markets retrieved from %s: %s", self.exchange.name, markets)
            actions = self._parse_markets(markets)
            self.on_event(actions)

    async def _fetch(self, session, url):
        async with session.get(url) as response:
            logging.debug("GET request: %s, status: %s", url, response.status)
            return await response.json()
    
    def _get_markets_uri(self):
        raise NotImplementedError()

    def _parse_markets(self, markets):
        raise NotImplementedError()

