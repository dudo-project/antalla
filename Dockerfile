FROM python:3.6

RUN mkdir /antalla
WORKDIR /antalla
COPY . /antalla
RUN pip install /antalla

ENTRYPOINT ["antalla"]

