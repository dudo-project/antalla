import json

import asyncio
import websockets
from sqlalchemy.orm import joinedload


from .. import db
from .. import models


def get_exchanges():
    exchanges = db.session.query(models.Exchange).options(joinedload("markets")).all()
    return [exchange.to_dict(include_markets=True) for exchange in exchanges]


async def send(websocket, action, data):
    message = dict(action=action, data=data)
    await websocket.send(json.dumps(message))


async def handle_message(websocket, message):
    action = message["action"]
    if action == "list-exchanges":
        exchanges = get_exchanges()
        await send(websocket, "exchanges", exchanges)

async def handle_connection(websocket, _path):
    while True:
        try:
            data = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            await handle_message(websocket, json.loads(data))
        except asyncio.TimeoutError:
            pass
        except websockets.exceptions.ConnectionClosed:
            break
