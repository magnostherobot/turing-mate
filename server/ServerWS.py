#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import random

def make_message(game_id, type, content):
    return json.dumps({'game_id': game_id, 'type': type, 'content': content})


currently_active = {}

async def main(websocket, path):
    while True:
        print("YEEET")

        dat = await websocket.recv()
        all_data = dat.split("|")

        for data in all_data:
            data = json.loads(data)
            type = data['type']
            path = data['game_id']

            if type == "register":
                # print("hello")
                if type not in currently_active:
                    currently_active[path] = {}
                    currently_active[path]['round'] = 1
                    currently_active[path]['answers'] = []
                    currently_active[path]['players'] = []
                    currently_active[path]['players'].append(websocket)
                else:
                    if started not in currently_active[path]:
                        currently_active[path]['players'].append(websocket)
            if type == 'start':
                random_int = random.randonInt(0, len(currently_active[path]['players']))
                for socket in currently_active[path]['players']:
                    await socket.send(make_message(path, "start", "start_ye_game"))
                await currently_active[path]['players'][random_int].send(make_message(path,"Choose a Question", "QUESTIONS HERE"))
            if type == "quit":
                for socket in currently_active[path]['players']:
                    await socket.send(make_message(path, "Quit", "End"))
                # Do Quit Activities
                if type in currently_active:
                    del currently_active[type]
            if type == "propogate_question":
                for socket in currently_active[path]['players']:
                    if socket != websocket:
                        await socket.send(make_message(path, "question", data['content']))
                currently_active[path]['answers'].append({})
            if type == "answer":
                # finish_round = False
                number = get_number(websocket)
                currently_active[path]['answers'][currently_active[path]['round']][number] = data['content']

                if len(currently_active[path]['answers'][currently_active[path]['round']]) == len(currently_active[path]['players']):
                    for socket in currently_active[path]['players']:
                        if socket != websocket:
                            await socket.send(make_message(path, "answer", currently_active[path]['content']))
                    currently_active[path]['round'] += 1
                    random_int = random.randonInt(0, len(currently_active[path]['players']))
                    for socket in currently_active[path]['players']:
                        await socket.send(make_message(path, "start", "start_ye_game"))
                    await currently_active[path]['players'][random_int].send(make_message(path,"Choose a Question", "QUESTIONS HERE"))
        # SEND CODE
        # await websocket.send(greeting)

start_server = websockets.serve(main, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
