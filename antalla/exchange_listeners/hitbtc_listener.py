import json
import logging

from datetime import datetime
from os import path

from dateutil.parser import parse as parse_date
import websockets
import aiohttp
import asyncio

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

@ExchangeListener.register("hitbtc")
class HitBTCListener(WebsocketListener):
    def __init__(self, exchange, on_event, ws_url=settings.HITBTC_WS_URL):
        super().__init__(exchange, on_event, ws_url)
        self._all_symbols = []

    def _get_uri(self, endpoint):
        return path.join(settings.HITBTC_API, endpoint)

    async def fetch_all_symbols(self, session):
        exchange_info = await self._fetch(session, self._get_uri(settings.HITBTC_API_SYMBOLS))
        all_symbols = []
        for symbol_info in exchange_info:
            all_symbols.append(dict(
                id=symbol_info["id"],
                baseCurrency=symbol_info["baseCurrency"],
                quoteCurrency=symbol_info["quoteCurrency"]
                ))
        return all_symbols

    async def get_markets(self):
        async with aiohttp.ClientSession() as session:
            symbols = await self.fetch_all_symbols(session)
            self._all_symbols = symbols
            markets = await self._fetch(session, self._get_uri(settings.HITBTC_API_MARKETS))
            logging.debug("markets retrieved from %s: %s", self.exchange.name, markets)
            actions = self._parse_markets(markets)
            self.on_event(actions)

    def _parse_market(self, market):
        for m in self._all_symbols:
            if m["id"] == market.upper():
                return (m["baseCurrency"], m["quoteCurrency"])
        return None

    def _parse_markets(self, markets):
        add_markets = []
        add_exchange_markets = []
        add_coins = []
        for market in markets:
            pair = self._parse_market(market["symbol"])
            if pair is not None:
                pair = list(pair)
                add_coins.extend([
                    models.Coin(symbol=pair[0]),
                    models.Coin(symbol=pair[1]),
                ])
                quoted_volume_id = pair[0]
                pair.sort()
                new_market = models.Market(
                    first_coin_id=pair[0],
                    second_coin_id=pair[1]
                )
                add_markets.append(new_market)
                add_exchange_markets.append(models.ExchangeMarket(
                    quoted_volume=float(market["volume"]),
                    quoted_volume_id=quoted_volume_id,
                    exchange_id=self.exchange.id,
                    first_coin_id=pair[0],
                    second_coin_id=pair[1],
                    quoted_vol_timestamp=parse_date(market["timestamp"])
                ))
            else:
                logging.warning("symbol not found in fetched symbols: %s", market["symbol"])
        return [ 
            actions.InsertAction(add_coins),
            actions.InsertAction(add_markets),
            actions.InsertAction(add_exchange_markets)
            ]