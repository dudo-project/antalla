.. antalla documentation master file, created by
   sphinx-quickstart on Mon Dec  2 11:13:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

antalla
=======

.. image:: _static/images/logo_2.svg

*antalla* fetches data from various exchanges and stores the orders and trades in
an SQL database.

The name comes from the Greek ανταλλαγή (antallagí), meaning “exchange”.

``antalla`` is part of the ``dudo`` project, which aims to foster
research and open-source software in the space of cryptocurrency
exchange design, auditability and market manipulation. Being the first
piece of software that is part of the project, the aim of antalla is to
facilitate cryptocurrency exchange market data analysis, ranging from
obtaining and storing the data to conducting analyses of locally hosted
real-time order books.

Even though the majority of cryptocurency exchanges provide lots of free
market data through APIs, it can be a tedious task normalising and
managing this data. Even more so, existing API wrappers often stop after
the normalisation of data and tend to be limited in the number of
exchanges they include. In fact, obtaining historical market data can be
very difficult unless one is willing to move to paid services.

antalla allows for easy addition of exchanges listeners, while also
offering features for data analysis, such as generating snapshots of the
state of a limit order book with any depth for a given market (or
markets) at specified time intervals. Of course, standard visualisation
capabilities are also included, e.g. real-time limit order book plots
for any depth.

Features
--------

-  ☒ Integration with major centralised exchanges (CEX) REST API and Web
   Socket streams
-  ☒ Locally reconstructable and real-time order books
-  ☒ Executed trade and aggregated order book data for large CEXs
-  ☒ Regular order book snapshots
-  ☒ Visualistions (e.g. order books, trades)
-  ☐ Extensive unit and integration tests

Installation
------------

The project requires Python 3.6 or above.

::

   git clone https://github.com/samwerner/antalla.git
   cd antalla
   pip install -e .

You should then be able to use the CLI, see ``antalla -h`` for the
available commands. Tests can be run with

::

   python setup.py test

Running antalla
---------------

An SQL database must be available to store the data. We recommend using
a PostgreSQL database for this purpose. The database URL can be set
through the ``DB_URL`` environment variable. For example

::

   export DB_URL="postgresql+psycopg2://antalla:antalla-password@127.0.0.1/antalla?sslmode=disable"

See the `SQLAlchemy
documentation <https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2>`__
about ``psycopg2`` for more details. about the URL scheme.

Initializing the database
~~~~~~~~~~~~~~~~~~~~~~~~~

Once the URL is set, the database can be initialized with the following
command:

::

   antalla init-db

Fetching initial market data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At any point in time, one can fetch the latest coin prices in USD, the
markets offered by each exchange, as well as the respective 24h traded
volume. The traded volume can also be normalised to USD in order to
allow for more informative comparisons.

All of the aforementioned can be fetched by running the command:

::

   antalla init-data

Each time ``init-data`` is run, the price and volume information is
updated in the db. This is equivalent to running the individual
commands:

::

   antalla markets
   antalla fetch-prices
   antalla norm-volume

Each subargument is further explained running:

::

   anatalla <subarg> --help

Exchange listeners
~~~~~~~~~~~~~~~~~~

Exchange listeners have been implemented for the following centralised
exchanges (CEXs) and decentralised exchanges (DEXs).

CEX exchange listeners:

-  ☒ Binance
-  ☒ Coinbase Pro
-  ☒ HitBTC
-  ☐ Bitfinex
-  ☐ Gemini
-  ☐ itBit
-  ☐ bitFlyer
-  ☐ Kraken
-  ☐ Poloniex
-  ☐ Bitrex
-  ☐ Bitstamp
-  ☐ OKex
-  ☐ CoinBene
-  ☐ Bitmex
-  ☐ Huobi Global

DEX exchange listeners:

-  ☒ IDEX
-  ☐ EthDelta
-  ☐ DDEX
-  ☐ Kyber Network
-  ☐ Oasis Dex

For each exchange the API key and secret can be set via environment
variables in the format ``<exchange>_API_KEY`` and
``<exchange>_API_SECRET``, respectively.

.. _running-antalla-1:

Running antalla
~~~~~~~~~~~~~~~

Once the DB is initialized, antalla can be ran with the following
command

::

   antalla run

The list of markets to listen for can be customized through the
``MARKET`` environment variable, which should be formatted as follow
``ETH_AURA,ETH_IDXM``.

Orderbook Snapshot Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

By setting the subparser argument

::

   antalla snapshot

a snapshot of each order book state will be computed and stored in the
order_book_snapshots table in the db. The interval between the snapshots
is set to the default value of 1 second. By setting the ``--exchange``
flag snapshots only for a set of specified exchanges will be generated.

Note: snapshots are only generated for periods during which there has
been aggregated order book data collected and no connection loss has
occurred. Hence, for each period between a connection and disconnect for
an exchange listener snapshots will be generated according to the set
snapshot interval.

Each snapshot contains relevant metrics for the current state of the
order book at the time taken. These metrics include:

- bid-ask spread
- bids count
- asks count
- bids volume
- asks volume
- bid price (mean) 
- ask price (mean)
- bid price (median)
- ask price (median)
- bid price (stddev)
- ask price (stddev)
- price and size of highest bid
- price and size of lowest ask

The order book depth per snapshot is configurable by setting the flag:
``--depth <percentage>``. The order book depth is specified as a
percentage relative to the mid price of the order book.

Alternatively, one may use the flag ``--quartile``, whereby snapshots
are computed for the upper quartile of bids and the lower quartile of
asks.

Note: by default, a snapshot will be generated for the quartile range of
the order book.

Connection Handling
~~~~~~~~~~~~~~~~~~~

Currently, there is no web or command line interface for providing an
overview of the state of connections to different exchanges. This will
very likely be added in antalla 1.0. Nontheless, all connections and
disconnections are logged in the ``events`` table in the db. In case of
a disconnect, the event is logged and antalla tries to reconnect to the
service. Features which make use of data (e.g. snapshots) are only
applied to data within time periods between a connection and a
diosconnect (or latest data in case no disconnect has occured). This is
important when analysing computed statistics, as values may be skewed if
they are based on data within early periods of a new connection widow if
previous values have been based on an earlier window.

Visualisations
~~~~~~~~~~~~~~

antalla comes with several built-in functionality for generating
different plots.

Order Book Plots
^^^^^^^^^^^^^^^^

For generating real-time order book plots, use the command:

::

   antalla plot-order-book --exchange <exchange> --market <market_pair>

Note: the ``--exchange`` and ``--market`` flags are required. Hence,
visualising one market’s order book requires one single process.

The plots are generated, plotting all buy and sell orders that lie in a
range of +-1% of the order book mid price. Alternatively one can
configure the ``OrderBookAnalyser`` defined in ``ob_analyser.py`` to use
a method (``_get_ob_quartiles``) plotting all bids which lie in the
upper quartile of the total bids and all asks which lie within the lower
quartile of the total asks.

Logo Credits
''''''''''''

The antalla logo was generated using
`launchaco <https://www.launchaco.com>`__: Montserrat-ExtraLight, by
Julieta Ulanovsky licensed under Open Font License. Icon by Vilahop


.. toctree::
   :maxdepth: 2
   :caption: Usage

   index.rst

.. toctree::
   :caption: Development
   :maxdepth: 2

   development/getting-started.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
