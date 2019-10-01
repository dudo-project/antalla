FROM python:3.6-alpine

RUN apk add postgresql-dev gcc musl-dev openblas lapack gfortran

RUN mkdir /antalla
COPY . /antalla
RUN pip install /antalla

ENTRYPOINT ["antalla"]

