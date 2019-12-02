.. antalla documentation master file, created by
   sphinx-quickstart on Mon Dec  2 11:13:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

antalla
=======

Introduction
------------

*antalla* is an open-source cryptocurrency exchange market data aggregation tool.
The name comes from the Greek ανταλλαγή (antallagí), meaning “exchange”.
*antalla* is part of the *dudo* project, which aims to foster
research and open-source software in the space of cryptocurrency
exchange design, auditability and market manipulation. Being the first
piece of software that is part of the project, the purpose of *antalla* is to
facilitate cryptocurrency exchange market data analysis, ranging from
obtaining and storing the data to conducting analyses of locally hosted
real-time order books.

Even though the majority of cryptocurency exchanges provide lots of free
market data through APIs, it can be a tedious task normalising and
managing this data. Even more so, existing API wrappers often stop after
the normalisation of data and tend to be limited in the number of
exchanges they include. In fact, obtaining historical market data can be
very difficult unless one is willing to move to paid services.

*antalla* allows for easy addition of exchanges listeners, while also
offering features for data analysis, such as generating snapshots of the
state of a limit order book with any depth for a given market (or
markets) at specified time intervals. Of course, standard visualisation
capabilities are also included, e.g. real-time limit order book plots
for any depth. By removing a substantial part of the engineering overhead, 
*antalla* seeks to stimulate new and innovative projects focused on cryptocurrency
order book analysis.

.. image:: _static/images/antalla.svg
   :scale: 60%
   :align: center


.. toctree::
   :maxdepth: 2
   :caption: Usage

   usage/requirements
   usage/quick-start
   usage/features
   usage/acknowledgements

.. toctree::
   :caption: Development
   :maxdepth: 2

   development/getting-started
   development/integrating-exchanges
   development/how-to-contribute


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
