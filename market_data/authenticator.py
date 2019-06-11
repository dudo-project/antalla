import asyncio
import websockets
import json
from . import settings

async def consumer_handler(websocket):
    #async for data in websocket:
      while True:
        data = await websocket.recv()
        # do something with data
        #print(f"< {data}")
        json_data = json.loads(data)
        print(json_data["event"] + ": " + json_data["payload"])

async def connect():
    async with websockets.connect(settings.IDEX_WS_URL) as websocket: 
        data = {
            'request': 'handshake', 
            'payload': json.dumps(dict(version="1.0.0", key=settings.IDEX_API_KEY))
        }
        
        message = json.dumps(data)
        await websocket.send(message)

        response = await websocket.recv()
        print(f"< {response}")

        response_json = json.loads(response)

        request_json = {
            "sid": response_json["sid"],
            "request": "subscribeToMarkets",
            "payload": json.dumps(dict(topics=settings.IDEX_MARKETS, events=settings.IDEX_EVENTS))
            }
        request = json.dumps(request_json)
        await websocket.send(request)
        response_2 = await websocket.recv()
        print(f"< {response_2}")
        
        await consumer_handler(websocket)


asyncio.get_event_loop().run_until_complete(connect())

    
