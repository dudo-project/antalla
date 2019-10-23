---
layout: default
---

Fetches data from various exchanges and stores the orders and trades in an SQL database.

The name comes from the Greek ανταλλαγή (antallagí), meaning "exchange". 

`antalla` is part of the `dudo` project, which aims to foster research and open-source software in the space of cryptocurrency exchange design, auditability and market manipulation. Being the first piece of software that is part of the project, the aim of antalla is to facilitate cryptocurrency exchange market data analysis, ranging from obtaining and storing the data to conducting analyses of locally hosted real-time order books. 

Even though the majority of cryptocurency exchanges provide lots of free market data through APIs, it can be a tedious task normalising and managing this data. Even more so, existing API wrappers often stop after the normalisation of data and tend to be limited in the number of exchanges they include. In fact, obtaining historical market data can be very difficult unless one is willing to move to paid services.

antalla allows for easy addition of exchanges listeners, while also offering features for data analysis, such as generating snapshots of the state of a limit order book with any depth for a given market (or markets) at specified time intervals. Of course, standard visualisation capabilities are also included, e.g. real-time limit order book plots for any depth. 

## Features
- [x] Integration with major centralised exchanges (CEX) REST API and Web Socket streams
- [x] Locally reconstructable and real-time order books
- [x] Executed trade and aggregated order book data for large CEXs
- [x] Regular order book snapshots
- [x] Visualistions (e.g. order books, trades)
- [ ] DB migrations using Python alembic
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

