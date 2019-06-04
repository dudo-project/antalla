from os import path
import json
import pkg_resources

from . import db, models, settings

def init_db(args):
    db.Base.metadata.create_all(db.engine)
    coins = pkg_resources.resource_string(settings.PACKAGE, path.join("fixtures","coins.json"))
    coins = json.loads(coins)

    for coin in coins:
        if models.Coin.query.get(coin["symbol"]):
            continue
        coin_model = models.Coin(**coin)
        db.session.add(coin_model)

    db.session.commit()