#

<img src="images/logo_2.svg" width="400">

[![CircleCI](https://circleci.com/gh/samwerner/antalla.svg?style=svg&circle-token=117f2cd4908b4eddd036d9b612e347420690efa9)](https://circleci.com/gh/samwerner/antalla)

Fetches data from various exchanges and stores the orders and trades in an SQL database.

The name comes from the Greek ανταλλαγή (antallagí) which meaning "exchange".

## Features
- [x] Integration with major centralised exchanges (CEX) REST API and Web Socket streams
- [x] Locally reconstructable and real-time order books
- [x] Executed trade and aggregated order book data for large CEXs
- [x] Regular order book snapshots
- [ ] Simple DB migrations using Python alembic
- [ ] Extensive unit and integration tests

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

### Fetching initial market data

At any point in time, one can fetch the latest coin prices in USD, the markets offered by each exchange, as well as the respective 24h traded volume.
The traded volume can also be normalised to USD in order to allow for more informative comparisons.

All of the aforementioned can be fetched by running the command:

```
antalla init-data
```

Each time `init-data` is run, the price and volume information is updated in the db.
This is equivalent to running the individual commands:

```
antalla markets
antalla fetch-prices
antalla norm-volume
```

Each subargument is further explained running:

```
anatalla <subarg> --help
```

### Exchange listeners

Exchange listeners have been implemented for the following centralised exchanges (CEXs) and decentralised exchanges (DEXs).

CEX exchange listeners:
- [x] Binance
- [x] Coinbase
- [ ] OKEX
- [x] HitBTC
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

### Orderbook Snapshot Analysis

By setting the subparser argument

```
antalla snapshot
```

a snapshot of each order book state will be computed and stored in the order_book_snapshots table in the db. The interval between the snapshots is set to the default value of 1 second. By setting the `--exchange` flag snapshots only for a set of specified exchanges will be generated.

Note: snapshots are only generated for periods where there has been aggregated order book data collected and no connection loss has occurred. Hence, for each period between a connection and disconnection for an exchange listener, snapshots will be generated according to the set snapshot interval.

Each snapshot contains relevant metrics for the current state of the order book at the time taken. These metrics include:
* bid-ask spread
* bids count
* asks count
* bids volume
* asks volume
* bid price (mean)
* ask price (mean)
* bid price (median)
* ask price (median)
* bid price (stddev)
* ask price (stddev)
* price and size of highest bid
* price and size of lowest ask 
* bid price (upper quartile)
* ask price (lower quartile)


### Visualisations

antalla comes with several built-in functionality for generating different plots.


#### Order Book Plots

For generating real-time order book plots, use the command:

```
antalla plot-order-book --exchange <exchange> --market <market_pair>
```

Note: the `--exchange` and `--market` flags are required. Hence, visualising one market's order book requires one single process.

The plots are generated, plotting all buy and sell orders that lie in a range of +-1% of the order book mid price. Alternatively one can configure the `OrderBookAnalyser` defined in `ob_analyser.py` to use a method (`_get_ob_quartiles`) plotting all bids which lie in the upper quartile of the total bids and all asks which lie within the lower quartile of the total asks.


[1]: https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2


##### Logo Credits
The antalla logo was generated using [launchaco](https://www.launchaco.com):
Montserrat-ExtraLight, by Julieta Ulanovsky licensed under Open Font License. Icon by Vilahop
