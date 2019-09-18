import aiohttp
import uuid
import json
import logging
import re
from datetime import datetime
from .base_factory import BaseFactory
from . import models
from . import actions
from .db import session 

DEFAULT_COMMIT_INTERVAL = 1

class ExchangeListener(BaseFactory):
    def __init__(self, exchange, on_event, markets):
        self._connected = False
        self.exchange = exchange
        self.on_event = on_event
        self.markets = self._get_existing_markets(markets)
        self.event_log = []
        self.commits = 0
        self._session_id = uuid.uuid4()
        self._all_symbols = None

    def _get_existing_markets(self, markets):
        existing_markets = []
        for market in markets:
            exchange_market = self._find_market(market)
            if exchange_market:
                existing_markets.append(exchange_market.original_name)
        return existing_markets

    def _find_market(self, market):
        pair = sorted(market.split("_"))
        return models.ExchangeMarket.query.get((pair[0], pair[1], self.exchange.id))

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

    def _parse_market_to_symbols(self, pair, all_symbols):
        """
        returns the individual coin symbols from a pair string of any possible length

        >>> from types import SimpleNamespace
        >>> symbols = ["BTC", "ETH", "WAVE", "USD"]
        >>> dummy_self = SimpleNamespace(all_symbols=symbols)
        >>> ExchangeListener._parse_market_to_symbols(dummy_self, "BTC_ETH", symbols)
        ('BTC', 'ETH')
        >>> ExchangeListener._parse_market_to_symbols(dummy_self, "BTCETH", symbols)
        ('BTC', 'ETH')
        >>> ExchangeListener._parse_market_to_symbols(dummy_self, "WAVEETH", symbols)
        ('WAVE', 'ETH')
        >>> ExchangeListener._parse_market_to_symbols(dummy_self, "USDWAVE", symbols)
        ('USD', 'WAVE')
        """   
        split_at = lambda string, n: (string[:n], string[n:])
        symbols = re.split("[_-]", pair)
        if len(symbols) == 2:
            return tuple(symbols)
        if len(pair) % 2 == 0:
            return split_at(pair, len(pair) // 2)
        for split_index in range(2, 10):
            symbols = split_at(pair, split_index)
            if all(sym in all_symbols for sym in symbols):
                return symbols
        raise Exception("unknown pair {} to parse".format(pair))

    @property
    def all_symbols(self):
        if not self._all_symbols:
            raise ValueError("_all_symbols is not set")
        return self._all_symbols

    def _log_event(self, market, connection_event, data_collected):
        pair = self._parse_market_to_symbols(market, self.all_symbols)
        event = models.Event(
            timestamp=datetime.now(),
            session_id=self._session_id,
            exchange_id=self.exchange.id,
            buy_sym_id=pair[0], 
            sell_sym_id=pair[1],
            connection_event=connection_event,
            data_collected=data_collected
        )
        action = actions.InsertAction([event])
        action.execute(session)
        if len(self.event_log) >= DEFAULT_COMMIT_INTERVAL:
            session.commit()
            self.commits += 1
            logging.info("event log commit[{}] - {} - {} event(s) committed to 'events' table".format(self.commits, self.exchange.name, len(self.event_log)))
            self.event_log.clear()
        else:
            self.event_log.append(action)

    def _log_disconnection(self):
        if not self._connected:
            return
        for market in self.markets:
            self._log_event(market, "disconnect", "all")
        self._connected = False
