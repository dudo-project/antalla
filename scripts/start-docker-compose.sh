#!/bin/bash

exec docker-compose up -d \
  --no-recreate \
  --scale coinbase=2 \
  --scale binance=2 \
  --scale idex=2
