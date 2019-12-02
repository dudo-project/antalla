Development
===========

This page is only useful if you are interested in developing antalla. If
you just want to use it, see `this page </>`__ instead.

--------------

Most of the administration tasks can be performed using the ``antalla``
command. Running the help command ``antalla -h`` provides information
about the different commands and parameters.

Database migrations
-------------------

Migrations use `alembic <https://github.com/sqlalchemy/alembic>`__. All
the regular `alembic
commands <https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration>`__
can be used from within the ``migrations`` directory, or alternatively
using ``antalla migrations`` instead of ``alembic``.

To simply get things running locally, the following command should
normally be enough.

::

   antalla migrations upgrade head
