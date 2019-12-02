
Features
========

Thus far, *antalla* has the following key features:

-  ☒ Integration with major centralised exchanges (CEX) REST API and Web
   Socket streams
-  ☒ Locally reconstructable and real-time order books
-  ☒ Executed trade and aggregated order book data for large CEXs
-  ☒ Regular order book snapshots
-  ☒ Visualistions (e.g. order books, trades)
-  ☐ Extensive unit and integration tests


Fetching Market Data
----------------------------

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
