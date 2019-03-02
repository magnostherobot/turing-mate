#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import random
from websockets.exceptions import ConnectionClosed

def make_message(game_id, type, content):
    return json.dumps({'game_id': game_id, 'type': type, 'content': content})


currently_active = {}

async def main(websocket, path):
    while True:
        print("-------YEEET-------")

        try:
            dat = await websocket.recv()
        except (ConnectionClosed):
            print("Connection is Closed")
            data = None
            break


        print("Received " + str(dat))
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
                    if "started" not in currently_active[path]:
                        currently_active[path]['players'].append(websocket)

                temp = data
                temp["type"] = "registered"
                await websocket.send(json.dumps(temp))
                print("Replied To Register Message")
            elif type == 'start':
                print("Received Start Message, Starting game for " +  path)
                if "started" not in currently_active[path]:
                    random_int = random.randint(0, len(currently_active[path]['players'])-1)
                    for socket in currently_active[path]['players']:
                        await socket.send(make_message(path, "started", "start_ye_game"))
                    await currently_active[path]['players'][random_int].send(make_message(path,"Choose a Question", "QUESTIONS HERE"))
                    currently_active[path]["started"] = True
            elif type == "quit":
                for socket in currently_active[path]['players']:
                    await socket.send(make_message(path, "Quit", "End"))
                # Do Quit Activities
                if type in currently_active:
                    del currently_active[type]
            elif type == "propogate_question":
                if currently_active[path]['started'] == True :
                    for socket in currently_active[path]['players']:
                        if socket != websocket:
                            await socket.send(make_message(path, "question", data['content']))
                    currently_active[path]['answers'].append({})
            elif type == "answer":
                if currently_active[path]['started'] == True :
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

            elif type == "echo":
                await websocket.send(json.dumps(data))
        # SEND CODE
        # await websocket.send(greeting)

start_server = websockets.serve(main, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
