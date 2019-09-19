#!/bin/bash

exec docker-compose up \
  --no-recreate \
  --scale idex=2 \
  --scale hitbtc=2 \
  --scale coinbase=2 \
  --scale binance=2
