FROM python:3.6-alpine

RUN apk add postgresql-dev gcc musl-dev openblas-dev python-dev lapack gfortran

RUN mkdir /antalla
COPY setup.py /antalla/setup.py
COPY bin /antalla/bin
RUN pip install /antalla
COPY . /antalla
RUN pip install /antalla

ENTRYPOINT ["antalla"]

