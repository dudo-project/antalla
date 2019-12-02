Requirements
============

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


An SQL database must be available to store the data. For this purpose, the 
recommended database to use is PostgreSQL. The database URL can be set
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
