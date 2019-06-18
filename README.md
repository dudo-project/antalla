#

<img src="images/logo.svg" width="300">

[![CircleCI](https://circleci.com/gh/samwerner/antalla.svg?style=svg&circle-token=117f2cd4908b4eddd036d9b612e347420690efa9)](https://circleci.com/gh/samwerner/antalla)

Fetches data from various exchanges and stores the orders and trades in an SQL database.

The name comes from the Greek ανταλλαγή (antallagí) which meaning "exchange".

## Installation

The project requires Python 3.6 or above.

```
git clone https://github.com/samwerner/antalla.git
cd antalla
pip install -e .
```

You should then be able to use the CLI, see `antalla -h` for the available commands.
Tests can be run with

```
python setup.py test
```

## Running antalla

An SQL database must be available to store the data.
We recommend using a PostgreSQL database for this purpose.
The database URL can be set through the `DB_URL` environment variable. For example

```
export DB_URL="postgresql+psycopg2://antalla:antalla-password@127.0.0.1/antalla?sslmode=disable"
```

See the [SQLAlchemy documentation][1] about `psycopg2` for more details. about the URL scheme.

### Initializing the database

Once the URL is set, the database can be initialized with the following command:

```
antalla init-db
```


### Exchange listeners

Exchange listeners have been implemented for the following centralised exchanges (CEXs) and decentralised exchanges (DEXs).

CEX exchange listeners:
- [x] Binance
- [x] Coinbase
- [ ] OKEX
- [ ] HitBTC
- [ ] Huobi Global

DEX exchange listeners:
- [x] IDEX
- [ ] EtherDelta
- [ ] token.store
- [ ] Paradex
- [ ] Radar Relay

For each exchange the API key and secret can be set via environment variables in the format `<exchange>_API_KEY` and `<exchange>_API_SECRET`, respectively.


### Running antalla

Once the DB is initialized, antalla can be ran with the following command

```
antalla run
```

The list of markets to listen for can be customized through the `MARKET` environment variable, which should be formatted as follow `ETH_AURA,ETH_IDXM`.

[1]: https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2
