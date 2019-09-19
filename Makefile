ENV ?= devlopment

ifeq ($(ENV), test)
DATABASE_NAME = antalla-test
else
DATABASE_NAME = antalla
endif

test:
	ENV=test nosetests --with-doctest

setup_db:
	createdb $(DATABASE_NAME) -O antalla
	PYTHON_ENV=$(ENV) antalla init-db
