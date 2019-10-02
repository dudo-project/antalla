#!/bin/bash

mkdir -p tmp
COLOR_FILE="tmp/current-color.txt"

current_color=$(cat $COLOR_FILE || "blue")
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

COMPOSE_HTTP_TIMEOUT=600 docker-compose -p "antalla-$current_color" down
