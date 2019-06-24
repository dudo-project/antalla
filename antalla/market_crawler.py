#%%
import json
import logging
from os import path
import pkg_resources

import aiohttp
from bs4 import BeautifulSoup

from . import settings


class MarketCrawler:
    def __init__(self):
        self._http_session = None
        self._marketcap_url = settings.COINMARKETCAP_URL
        coinmarket_filepath = path.join("fixtures", "coinmarketcap-mappings.json")
        file_content = pkg_resources.resource_string(settings.PACKAGE, coinmarket_filepath)
        self._coins = {v["symbol"]: v["name"] for v in json.loads(file_content)}
        self._prices = {}

    async def get_price(self, symbol):
        if not self._prices:
            await self._fetch_prices()
        price = self._prices.get(symbol, 0)
        if not price:
            logging.info("coin name not found for: %s", symbol)
        return price

    def get_coin_name(self, symbol):
        '''
        returns the full name for a given token symbol using the specified mapping

        >>> crawler = MarketCrawler()
        >>> crawler.get_coin_name('BTC')
        'Bitcoin'
        >>> crawler.get_coin_name('ZEC')
        'Zcash'
        >>> crawler.get_coin_name('ZRX')
        '0x'
        >>> crawler.get_coin_name('NANO')
        'Nano'
        '''
        return self._coins.get(symbol)

    async def _fetch_prices(self):
        async with aiohttp.ClientSession() as session:
            text = await self._fetch(session, settings.COINMARKETCAP_URL)
            soup = BeautifulSoup(text, features="html.parser")
            logging.debug("fetched HTML for all USD prices: %s", soup)
        tbody = soup.find("table", {"id": "currencies-all"}).tbody
        for row in tbody.find_all("tr"):
            symbol = row.find("td", {"class": "col-symbol"}).text
            price = float(row.find("a", {"class": "price"})["data-usd"])
            self._prices[symbol] = price

    async def _fetch(self, session, url):
        async with session.get(url) as response:
            logging.debug("GET request: %s, status: %s", url, response.status)
            return await response.text()
