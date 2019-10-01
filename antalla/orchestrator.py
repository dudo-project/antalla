import asyncio
from typing import List, Dict
import logging

from .exchange_listener import ExchangeListener
from . import db
from . import models
from .actions import Action, InsertAction, UpdateAction

DEFAULT_COMMIT_INTERVAL = 100

import aiohttp

class Orchestrator:
    def __init__(self,
                 exchange_names,
                 session=None,
                 commit_interval=DEFAULT_COMMIT_INTERVAL,
                 event_type=None,
                 markets: Dict[str, List[str]] = None):
        if session is None:
            session = db.session
        if markets is None:
            markets = {}
        self.session = session
        self.commit_interval = commit_interval
        self._rows_modified = 0
        self._stats = dict(commits=0, inserts=0, updates=0)
        self.exchange_listeners = [
            self._create_exchange_listener(name, event_type, markets=markets.get(name))
            for name in exchange_names
        ]

    def _create_exchange_listener(self, name, event_type, markets: List[str] = None):
        exchange = self.session.query(models.Exchange).filter_by(name=name).one()
        logging.info("creating exchange listener for '%s': %s (event_type=%s)",
                     name, exchange, event_type)
        kwargs = dict(event_type=event_type)
        if markets is not None:
            kwargs["markets"] = markets
        return ExchangeListener.create(name, exchange, self._on_event, **kwargs)

    async def start(self):
        await asyncio.gather(*[e.listen() for e in self.exchange_listeners])

    async def get_markets(self):
        await asyncio.gather(*[e.get_markets() for e in self.exchange_listeners])

    def stop(self):
        for exchange_listener in self.exchange_listeners:
            exchange_listener.stop()
            logging.info("stop exchange listener: %s", exchange_listener.exchange)
        self.session.commit()

    def _on_event(self, actions: List[Action]):
        for action in actions:
            self._track_actions(action)
            self._rows_modified += action.execute(self.session)

        if self._rows_modified >= self.commit_interval:
            logging.info(("commit number [%s]: committing changes "
                "Insert Actions: %s, Update Actions: %s"), 
                self._stats["commits"], self._stats["inserts"], self._stats["updates"])
            self.session.commit()
            self._rows_modified = 0
            self._stats["commits"] += 1
            self._stats["inserts"] = 0
            self._stats["updates"] = 0
            
    def _track_actions(self, action):
        if isinstance(action, InsertAction):
            self._stats["inserts"] += 1
        elif isinstance(action, UpdateAction):
            self._stats["updates"] += 1