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
        self._fetched_prices = False

    async def __aenter__(self):
        self._http_session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, arg_1, arg_2, arg_3):
        await self._http_session.close()

    async def get_price(self, symbol):
        coin_name = self.get_coin_name(symbol)
        if not coin_name:
            logging.info("coin name not found for: %s", symbol)
            return 0
        if self._fetched_prices == False:
            text = await self._fetch(self._http_session, settings.COINMARKETCAP_URL)
            self._soup = BeautifulSoup(text)
            logging.debug("fetched HTML for all USD prices: %s", self._soup)
            self._fetched_prices = True
        coin_uri = self._soup.find("td", {"data-sort": coin_name}).span.a["href"]
        coin_uri = coin_uri + "#markets"
        price = self._soup.find("a", {"href": coin_uri})["data-usd"]   
        return float(price)

    def get_coin_name(self, symbol):
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