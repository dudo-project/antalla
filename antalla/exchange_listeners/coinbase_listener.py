import json
import logging

from datetime import datetime

from dateutil.parser import parse as parse_date
import websockets
import aiohttp

from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

@ExchangeListener.register("coinbase")
class CoinbaseListener(WebsocketListener):
    def __init__(self, exchange, on_event, ws_url=settings.COINBASE_WS_URL):
        super().__init__(exchange, on_event, ws_url)
        self._format_markets()

    def _parse_message(self, message):
        event, payload = message["type"], message
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []
    
    def _parse_received(self, received):
        return [actions.InsertAction([self._convert_raw_order(received)])]

    def _convert_raw_order(self, received):
        order = models.Order(
            timestamp=parse_date(received["time"]),
            buy_sym_id=received["product_id"].split("-")[0],
            sell_sym_id=received["product_id"].split("-")[1],
            exchange_order_id=received["order_id"],
            exchange=self.exchange,
            side=received["side"],
            order_type=received["order_type"]
        )
        if "funds" in received:
            order.funds = [self._new_market_order_funds(
                received["time"], 
                received["funds"],
                received["order_id"]
                )]
        else:
            order.price = float(received["price"])
            order.sizes = [self._new_order_size(received["time"], received["size"], received["order_id"])]
        return order

    def _parse_open(self, open_order):
        # only for orders that are not fully filled immediately 
        return [actions.InsertAction([self._convert_raw_open_order(open_order)])]

    def _convert_raw_open_order(self, open_order):
        return models.Order(
            timestamp=parse_date(open_order["time"]),
            buy_sym_id=open_order["product_id"].split("-")[0],
            sell_sym_id=open_order["product_id"].split("-")[1],
            exchange_order_id=open_order["order_id"],
            side=open_order["side"],
            price=float(open_order["price"]),
            sizes=[self._new_order_size(
                open_order["time"],
                open_order["remaining_size"],
                open_order["order_id"]
            )],
            exchange=self.exchange
        )
        
    def _parse_done(self, order):
        # order is no longer on the order book; message sent for fully filled or cancelled orders
        # market orders will not have remaining_size or price field as they are never in order book
        update_fields = {}
        update_fields["remaining_size"] = order["remaining_size"]
        if order["reason"] == "filled":
            update_fields["filled_at"] = parse_date(order["time"])
        elif order["reason"] == "canceled":
            update_fields["cancelled_at"] = parse_date(order["time"])
        else:
            logging.error("failed to process order: %s", order)
        return [actions.UpdateAction(
            models.Order, 
            {"exchange_order_id": order["order_id"], "exchange_id": self.exchange.id},
            update_fields
            )] 

    def _new_order_size(self, timestamp, size, order_id):
        return models.OrderSize(
            timestamp=parse_date(timestamp),
            exchange_order_id=order_id,
            size=float(size)
        )

    def _new_market_order_funds(self, timestamp, funds, order_id):
        return models.MarketOrderFunds(
            timestamp=parse_date(timestamp),
            exchange_order_id=order_id,
            funds=float(funds)
        )

    def _parse_change(self, update):
        # an order has changed: result of self-trade prevention adjusting order size or available funds
        if "new_size" in update:
            return [actions.InsertAction([self._new_order_size(
                update["time"],
                update["new_size"],
                update["order_id"]
            )])]
        elif "new_funds" in update:
            return [actions.InsertAction([self._new_market_order_funds(
                update["time"],
                update["new_funds"],
                update["order_id"]
            )])]
        else:
            # FIXME: raise an exception
            logging.debug("failed to process order: %s", update)
        return []

    def _parse_match(self, match):
        # a trade occurred between two orders 
        return [actions.InsertAction([self._convert_raw_match(match)])]

    def _convert_raw_match(self, match):
        return models.Trade(
            timestamp=parse_date(match["time"]),
            exchange=self.exchange,
            trade_type=match["side"],
            buy_sym_id=match["product_id"].split("-")[0],
            sell_sym_id=match["product_id"].split("-")[1],
            maker_order_id=match["maker_order_id"],
            taker_order_id=match["taker_order_id"],
            price=float(match["price"]),
            size=float(match["size"])
        )

    async def _setup_connection(self, websocket):
        await self._send_message(websocket, "subscribe", self._all_markets, settings.COINBASE_CHANNELS)         

    def _format_markets(self):
        self._all_markets = []
        for market in settings.COINBASE_MARKETS:
            self._all_markets.append('-'.join(market.split("_")))
    
    async def _send_message(self, websocket, request, product_ids, channels):
        data = dict(type=request, product_ids=product_ids, channels=channels)
        message = json.dumps(data)
        logging.debug("> %s: %s", request, product_ids)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)