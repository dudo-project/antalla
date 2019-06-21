#%%
import aiohttp
import json
import logging
from os import path

from bs4 import BeautifulSoup
import urllib.parse
from . import settings

FIXTURES_PATH = path.join(path.dirname(__file__), "fixtures")

class MarketCrawler:
    def __init__(self):
        self._http_session = None
        self._marketcap_url = settings.COINMARKETCAP_URL
        with open(path.join(FIXTURES_PATH, "coinmarketcap-mappings.json")) as f:
            self._coins = json.load(f)
        
    async def __aenter__(self):
        self._http_session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, arg_1, arg_2, arg_3):
        self._http_session = None

    async def get_price(self, symbol):
        coin_name = self._lookup_coin(symbol)
        if not coin_name:
            logging.info("coin name not found for: %s", symbol)
            return 0
        req_uri = '/'.join([self._marketcap_url, coin_name.lower()])
        print(req_uri)
        text = await self._fetch(self._http_session, req_uri)
        print(symbol)
        soup = BeautifulSoup(text)
        price = soup.find("span", {"id": "quote_price"})["data-usd"]
        return float(price)

    def _lookup_coin(self, symbol):
        '''
        returns the full name for a given token symbol using the specified mapping

        >>> crawler = MarketCrawler()
        >>> crawler._lookup_coin('BTC')
        'Bitcoin'
        >>> crawler._lookup_coin('ZEC')
        'Zcash'
        >>> crawler._lookup_coin('ZRX')
        '0x'
        >>> crawler._lookup_coin('NANO')
        'Nano'
        '''
        for c in self._coins:
            if (c["symbol"] == symbol):
                return c["name"]
        return None
        
    async def _fetch(self, session, url):
        async with session.get(url) as response:
            logging.debug("GET request: %s, status: %s", url, response.status)
            return await response.text()