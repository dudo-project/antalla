#!/bin/bash

COMPOSE_HTTP_TIMEOUT=600 \
  exec docker-compose up -d \
  --no-recreate \
  --scale coinbase=2 \
  --scale binance=2 \
  --scale idex=2
