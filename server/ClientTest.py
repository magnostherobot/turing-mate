# import requests
# import json
# import sys
# import argparse
#
#
# def send(message, route):
#     res = ""
#     try:
#         res = requests.post(endpoint + route, message)
#     except requests.exceptions.ConnectionError:
#         print("Cannot connect to Prosecutor Service, exiting")
#         sys.exit(0)
#
#     return res
#
#
# if __name__ == "__main__":
#     endpoint = "http://127.0.0.1:5000/flargs"
#     res = send("yeet",endpoint)
#     print(res.content.decode())


#!/usr/bin/env python

# WS client example

import asyncio
import websockets

async def hello():
    async with websockets.connect(
            'ws://138.251.29.56:8765') as websocket:
        name = input("What's your name? ")

        await websocket.send(name)
        print(f"> {name}")

        greeting = await websocket.recv()
        print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())
