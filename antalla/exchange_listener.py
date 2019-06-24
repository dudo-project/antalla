import aiohttp
import json
import logging
from .base_factory import BaseFactory
from . import models

class ExchangeListener(BaseFactory):
    def __init__(self, exchange, on_event, markets):
        self.exchange = exchange
        self.on_event = on_event
        self.markets = self._get_existing_markets(markets)

    def _get_existing_markets(self, markets):
        existing_markets = []
        for market in markets:
            if self._find_market(market):
                existing_markets.append(market)
        return existing_markets

    def _find_market(self, market):
        first_coin, second_coin = market.split("_")
        return models.ExchangeMarket.query.get((first_coin, second_coin, self.exchange.id))

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

    def _parse_market(self, pair, all_symbols):
        """
        returns the individual coin symbols from a pair string of any possible length

        >>> from types import SimpleNamespace
        >>> symbols = ["BTC", "ETH", "WAVE", "USD"]
        >>> dummy_self = SimpleNamespace(all_symbols=symbols)
        >>> ExchangeListener._parse_market(dummy_self, "BTC_ETH", symbols)
        ('BTC', 'ETH')
        >>> ExchangeListener._parse_market(dummy_self, "BTCETH", symbols)
        ('BTC', 'ETH')
        >>> ExchangeListener._parse_market(dummy_self, "WAVEETH", symbols)
        ('WAVE', 'ETH')
        >>> ExchangeListener._parse_market(dummy_self, "USDWAVE", symbols)
        ('USD', 'WAVE')
        """   
        split_at = lambda string, n: (string[:n], string[n:])
        symbols = pair.split("_")
        if len(symbols) == 2:
            return tuple(symbols)
        if len(pair) % 2 == 0:
            return split_at(pair, len(pair) // 2)
        for split_index in range(2, 10):
            symbols = split_at(pair, split_index)
            if all(sym in all_symbols for sym in symbols):
                return symbols
        raise Exception("unknown pair {} to parse".format(pair))