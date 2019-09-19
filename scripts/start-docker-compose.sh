#!/bin/bash

exec docker-compose up \
  --no-recreate \
  --scale coinbase=2 \
  --scale binance=2
