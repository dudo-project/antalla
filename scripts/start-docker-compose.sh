#!/bin/bash

mkdir -p tmp
COLOR_FILE="tmp/current-color.txt"

if [ -f $COLOR_FILE ]; then
  current_color=$(cat $COLOR_FILE)
else
  current_color="blue"
fi

if [ $current_color = "blue" ]; then
  color="green"
else
  color="blue"
fi

COMPOSE_HTTP_TIMEOUT=600 \
  docker-compose -p "antalla-$color" up -d \
  --no-recreate \
  --scale coinbase=2 \
  --scale binance=2 \
  --scale idex=2

echo "$color" > $COLOR_FILE

sleep 10

COMPOSE_HTTP_TIMEOUT=600 docker-compose -p "antalla-$current_color" down
