Getting Started
===============

This page contains the necessary information to get started with *antalla*
development.

Dependencies
------------

Please make sure you first follow the steps in :ref:`requirements`.
Although not required, we suggest you setup a `venv`_ for the project.
Then, to install all required dependencies, you can run

.. code-block:: shell

  pip install -r requirements.txt


Setting up the databases
------------------------

You will need to setup a PostgreSQL database for both development and tests.
If you want to avoid changing too much configuration, you can set it up with
the following attributes.

+------------+--------------+
| Property   | Value        |
+============+==============+
| owner      | antalla      |
+------------+--------------+
| password   | antalla      |
+------------+--------------+
| dev db     | antalla      |
+------------+--------------+
| test db    | antalla-test |
+------------+--------------+
| encoding   | utf-8        |
+------------+--------------+

You can set it up with the following commands (run as postgres or another PostgreSQL admin user)

.. code-block:: sh

    createuser antalla -P # type antalla as a password
    createdb -O antalla antalla
    createdb -O antalla antalla-test

If you prefer to use another database, you can always set the `DATABASE_URL`
environment variable as needed. Otherwise, the `ENV` environment
variable is used to control which database to use. It should be set to `TEST`
when running tests.
Migrations must be run on both databases and data should be initialized in
the development database.

.. code-block:: sh

    antalla migrations upgrade head
    antalla init-data
    ENV=test antalla migrations upgrade head


Testing
-------

At this point, all the unit test should be passing.
Tests can be run using

.. code-block:: sh

    make test

If you need to debug a single test, you can do so with the following command

.. code-block:: sh

    ENV=test nosetests tests.test_file:TestClass.test_method

.. _venv: https://docs.python.org/3/tutorial/venv.html