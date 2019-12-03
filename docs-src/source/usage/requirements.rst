.. _requirements:

Requirements
============

Database
--------

This project currently only supports PostgreSQL as a backend.
Before installing Python packages, you will need to have the development
libraries of PostgreSQL. For Ubuntu, run the following command

.. code-block:: shell

   sudo apt install libpq-dev

*antalla*
---------

The project requires Python 3.6 or above. In order to get started clone the project from Github 
and install all dependencies:

::

   git clone https://github.com/samwerner/antalla.git
   cd antalla
   pip install -e .

You should then be able to use the CLI, see ``antalla -h`` for the
available commands. Each subargument is further explained running:

::

   anatalla <subarg> --help


The database URL can be set
through the ``DB_URL`` environment variable. For example

::

   export DB_URL="postgresql+psycopg2://antalla:antalla-password@127.0.0.1/antalla?sslmode=disable"

See the `SQLAlchemy
documentation <https://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2>`__
about ``psycopg2`` for more details about the URL scheme.


Once the database setup is completed, you can run the *antalla* unit tests, which should all pass.
Tests can be run with the command:

::

   python setup.py test
