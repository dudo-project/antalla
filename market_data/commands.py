import signal
from os import path
import json
import pkg_resources
import asyncio

from . import db, models, settings
from .exchange_listener import ExchangeListener
from .orchestrator import Orchestrator


def init_db(args):
    db.Base.metadata.create_all(db.engine)
    fixtures = [("coins.json", models.Coin, "symbol"),
                ("exchanges.json", models.Exchange, "name")]
    for filename, Model, column in fixtures:
        filepath = path.join("fixtures", filename)
        entities = pkg_resources.resource_string(settings.PACKAGE, filepath)
        entities = json.loads(entities)

        for entity in entities:
            if Model.query.filter_by(**{column: entity[column]}).first():
                continue
            model = Model(**entity)
            db.session.add(model)

        db.session.commit()


def run(args):
    if args["exchanges"]:
        exchanges = args["exchanges"]
    else:
        exchanges = ExchangeListener.registered()
    orchestrator = Orchestrator(exchanges)
    def handler(_signum, _frame):
        orchestrator.stop()
    signal.signal(signal.SIGINT, handler)
    try:
        asyncio.get_event_loop().run_until_complete(orchestrator.start())
    except KeyboardInterrupt:
        orchestrator.stop()
