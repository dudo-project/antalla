import re
import json
from collections import defaultdict
from antalla import db, models


def get_markets(exchange, symbol):
    markets = db.session.execute(
        f"""select original_name from {models.ExchangeMarket.__tablename__} em 
        inner join {models.Exchange.__tablename__} e on em.exchange_id = e.id
        where e.name=:exchange and (first_coin_id=:symbol or second_coin_id=:symbol)""",
        {"symbol": symbol.upper(), "exchange": exchange.lower()},
    )
    markets = list(markets)
    if len(markets) == 0:
        return 0
    # parsed_markets= []
    exchange_markets = defaultdict(list)
    for row in markets:
        market = parse_market_from_symbol(row[0], symbol.upper())
        # parsed_markets.append(market)
        exchange_markets[exchange].append(market)
    file = exchange + "_" + symbol.lower() + ".json"
    with open(file, "w") as f:
        json.dump(exchange_markets, f)
        # for item in parsed_markets:
        #    f.write("%s\n" % item)


def parse_market_from_symbol(market, symbol):
    # TODO: add doctest
    pair = re.split("[-_]", market)
    if len(pair) == 1:
        if market[0 : len(symbol)] == symbol:
            return symbol + "_" + market[len(symbol) :]
        else:
            return market[0 : (len(market) - len(symbol))] + "_" + symbol
    return pair[0] + "_" + pair[1]
