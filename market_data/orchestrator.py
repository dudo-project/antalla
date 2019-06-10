import asyncio

from .exchange_listener import ExchangeListener
from . import db
from . import models


DEFAULT_COMMIT_INTERVAL = 100


class Orchestrator:
    def __init__(self, exchange_names, session=None, commit_interval=DEFAULT_COMMIT_INTERVAL):
        if session is None:
            session = db.session
        self.session = session
        self.commit_interval = commit_interval
        self._rows_modified = 0
        self.exchange_listeners = [self._create_exchange_listener(name)
                                   for name in exchange_names]

    def _create_exchange_listener(self, name):
        exchange = self.session.query(models.Exchange).filter_by(name=name).one()
        return ExchangeListener.create(name, exchange, self._on_event)

    async def start(self):
        await asyncio.gather(*[e.listen() for e in self.exchange_listeners])

    def stop(self):
        for exchange_listener in self.exchange_listeners:
            exchange_listener.stop()
        self.session.commit()

    def _on_event(self, actions):
        if not actions:
            return

        for action in actions:
            self._rows_modified += action.execute(self.session)

        if self._rows_modified >= self.commit_interval:
            self.session.commit()
            self._rows_modified = 0
