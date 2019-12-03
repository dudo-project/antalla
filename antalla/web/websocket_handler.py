import json
import logging

import asyncio
import websockets
from sqlalchemy.orm import joinedload


from .. import db
from .. import models
from ..ob_analyser import OrderBookAnalyser


def get_exchanges():
    exchanges = db.session.query(models.Exchange).options(joinedload("markets")).all()
    return [exchange.to_dict(include_markets=True) for exchange in exchanges]


class ConnectionHandler:
    def __init__(self, websocket):
        self.websocket = websocket
        self.subscriptions = {}

    async def send(self, action, data):
        message = dict(action=action, data=data)
        await self.websocket.send(json.dumps(message))

    async def handle_subscribe_depth(self, data):
        if not ("exchange" in data and "buy_sym" in data and "sell_sym"):
            logging.warning("invalid subcription request %s", data)
            return
        ob_analyzer = OrderBookAnalyser(data["buy_sym"], data["sell_sym"], data["exchange"])
        self.subscriptions["depth"] = dict(analyzer=ob_analyzer)

    async def handle_list_exchanges(self, _data):
        exchanges = get_exchanges()
        await self.send("exchanges", exchanges)

    async def handle_message(self, message):
        action = message["action"]
        handler = getattr(self, "handle_" + action.replace("-", "_"), None)
        if handler:
            await handler(message.get("data", {}))
        else:
            logging.warning("unknown action %s", action)

    async def handle_depth_subscription(self, params):
        ob_analyzer = params["analyzer"]
        depth_data = ob_analyzer.generate_depth_data()
        await self.send("depth", depth_data)

    async def handle_subscriptions(self):
        for subscription_name, params in self.subscriptions.items():
            func = getattr(self, "handle_{0}_subscription".format(subscription_name))
            await func(params)

    async def run(self):
        while True:
            try:
                await self.handle_subscriptions()
                data = await asyncio.wait_for(self.websocket.recv(), timeout=1)
                await self.handle_message(json.loads(data))
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                break


async def handle_connection(websocket, _path):
    handler = ConnectionHandler(websocket)
    await handler.run()
