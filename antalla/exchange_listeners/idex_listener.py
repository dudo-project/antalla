from typing import List
import json
import logging
from datetime import datetime
import time

from dateutil.parser import parse as parse_date
from sqlalchemy.sql.expression import tuple_
import websockets

from .. import db
from .. import settings
from .. import models
from .. import actions
from ..exchange_listener import ExchangeListener
from ..websocket_listener import WebsocketListener

import aiohttp


MAX_MARKETS = 100


@ExchangeListener.register("idex")
class IdexListener(WebsocketListener):
    def __init__(self,
                 exchange,
                 on_event,
                 session=db.session,
                 markets=settings.IDEX_MARKETS,
                 ws_url=settings.IDEX_WS_URL,
                 event_type=None,
                 max_markets=MAX_MARKETS):
        self.max_markets = max_markets
        self.session = session
        super().__init__(exchange, on_event, markets, ws_url, event_type)
        self._all_symbols = []
        self._parse_all_symbols()

    def _get_existing_markets(self, markets: List[str]) -> List[str]:
        def get_market_pk(market):
            pair = sorted(market.split("_"))
            return (pair[0], pair[1], self.exchange.id)
        market_pks = [get_market_pk(market) for market in markets]
        results = self.session.query(models.ExchangeMarket) \
                      .filter(tuple_(models.ExchangeMarket.first_coin_id,
                                     models.ExchangeMarket.second_coin_id,
                                     models.ExchangeMarket.exchange_id).in_(market_pks)) \
                      .order_by(models.ExchangeMarket.volume_usd.desc()) \
                      .limit(self.max_markets) \
                      .all()
        return [result.original_name for result in results]

    def _parse_all_symbols(self):
        for market in self.markets:
            first_market, second_market = market.split("_")
            self._all_symbols.append(first_market)
            self._all_symbols.append(first_market)

    async def _send_message(self, websocket, request, payload, **kwargs):
        data = dict(request=request, payload=json.dumps(payload))
        data.update(kwargs)
        message = json.dumps(data)
        logging.debug("> %s: %s", request, payload)
        await websocket.send(message)
        response = await websocket.recv()
        logging.debug("< %s", response)
        return json.loads(response)

    def _get_events(self):
        return self._compute_events(self.event_type, settings.IDEX_EVENTS)

    async def _setup_connection(self, websocket):
        handshake_data = dict(version="1.0.0", key=settings.IDEX_API_KEY)
        handshake_res = await self._send_message(websocket, "handshake", handshake_data)
        subscription_data = dict(topics=self.markets, events=self._get_events())
        await self._send_message(websocket, "subscribeToMarkets",
                                 subscription_data, sid=handshake_res["sid"])
        for event in settings.IDEX_EVENTS:
            for market in self.markets:
                data_collected = self._get_event_data_collected(event)
                self._log_event(market, "connect", data_collected)

    def _get_event_data_collected(self, data_type):
        if data_type == "market_orders":
            return "orders"
        elif data_type == "market_trades":
            return "trades"
        elif data_type == "market_cancels":
            return "order_cancels"
        else:
            logging.debug(" {} - unknown event type for 'data collected' - {}".format(self.exchange.name, data_type))
            return "Unknown"

    def _parse_message(self, message):
        event, payload = message["event"], json.loads(message["payload"])
        func = getattr(self, f"_parse_{event}", None)
        if func:
            return func(payload)
        return []

    def _parse_market_orders(self, payload):
        buy_sym, sell_sym = payload["market"].split("_")
        orders = []
        order_sizes = []
        for order in payload["orders"]:
            orders.append(self._convert_raw_order(order, buy_sym, sell_sym))
            order_sizes.append(self._new_order_size(
                order["createdAt"], float(order["amountBuy"]), order["hash"]))
        return [actions.InsertAction(orders), actions.InsertAction(order_sizes)]

    def _convert_raw_order(self, raw_order, buy_sym, sell_sym):
        return models.Order(
            timestamp=parse_date(raw_order["createdAt"]),
            exchange_id=self.exchange.id,
            buy_sym_id=buy_sym,
            sell_sym_id=sell_sym,
            price=float(raw_order["amountSell"])/float(raw_order["amountBuy"]),
            side="buy",
            user=raw_order["user"],
            exchange_order_id=raw_order["hash"],
        )

    def _new_order_size(self, timestamp, size, order_id):
        return models.OrderSize(
            timestamp=parse_date(timestamp),
            exchange_id=self.exchange.id,
            exchange_order_id=order_id,
            size=float(size)
        )

    def _parse_market_cancels(self, payload):
        update_actions = []
        for cancel in payload["cancels"]:
                update_actions.append(actions.UpdateAction(
                    models.Order,
                    {"exchange_order_id": cancel["orderHash"], "exchange_id": self.exchange.id},
                    {"cancelled_at": parse_date(cancel["createdAt"])}
                ))
        return update_actions

    def _parse_market_trades(self, payload):  
        update_actions = []
        buy_sym, sell_sym = payload["market"].split("_")
        trades = []
        for trade in payload["trades"]:
            trades.append(self._convert_raw_trade(trade, buy_sym, sell_sym))
            update_actions.append(actions.UpdateAction(
                    models.Order,
                    {"exchange_order_id": trade["orderHash"], "exchange_id": self.exchange.id},
                    {"filled_at": datetime.fromtimestamp(trade["timestamp"])}
                ))
        insert_actions = [actions.InsertAction(trades)]
        return insert_actions + update_actions

    def _convert_raw_trade(self, raw_trade, buy_sym, sell_sym):
        return models.Trade(
            timestamp=datetime.fromtimestamp(raw_trade["timestamp"]),
            trade_type=raw_trade["type"],
            exchange_id=self.exchange.id,
            # idex market pairs are not following the normal convention, i.e. ETH/BTC does not mean price is expressed in BTC (but ETH)
            # hence, this is modified below by switching the pairs
            buy_sym_id=sell_sym,
            sell_sym_id=buy_sym,
            maker=raw_trade["maker"],
            taker=raw_trade["taker"],
            exchange_order_id=raw_trade["orderHash"],
            gas_fee=float(raw_trade["gasFee"]),
            price=float(raw_trade["price"]),
            size=float(raw_trade["amount"]),
            total=float(raw_trade["total"]),
            buyer_fee=float(raw_trade["buyerFee"]),
            seller_fee=float(raw_trade["sellerFee"]),
            exchange_trade_id=str(raw_trade["tid"])
        )

    def _get_markets_uri(self):
        return (
            settings.IDEX_API + "/" +
            settings.IDEX_API_MARKETS
            )

    def _parse_markets(self, markets):
        # volume is normalised to USD and market pairs are sorted to avoid reversed duplicates in db
        new_markets = []
        exchange_markets = []
        coins = []
        for key in markets.keys():
            market = key.split("_")
            if len(market) == 2:
                coins.extend([
                    models.Coin(symbol=market[0]),
                    models.Coin(symbol=market[1]),
                ])
                quoted_volume_id = market[0]
                market.sort()
                exchange_markets.append(models.ExchangeMarket(
                    quoted_volume=float(markets[key].get(quoted_volume_id)),
                    quoted_volume_id=quoted_volume_id,
                    exchange_id=self.exchange.id,
                    first_coin_id=market[0],
                    second_coin_id=market[1],
                    quoted_vol_timestamp=datetime.now(),
                    original_name=key
                ))
                new_market = models.Market(
                    first_coin_id=market[0],
                    second_coin_id=market[1],
                )
                new_markets.append(new_market)
            else:
                logging.warning("parse markets for '{}' - invalid market format: '{}' is not a pair of markets - IGNORE".format(self.exchange.name, market))
        return [
            actions.InsertAction(coins),
            actions.InsertAction(new_markets),
            actions.InsertAction(exchange_markets)
        ]
