#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import random
from websockets.exceptions import ConnectionClosed

def get_question_selection():
    return [ 'Q1', 'Q2', 'Q3' ]

class Player:
    def __init__(self, id, sock):
        self.id = id
        self.sock = sock
        self.game = None

    def kick(self):
        self.sock.close()

    async def send(self, msg):
        await self.sock.send(msg)

    async def receive(self):
        try:
            data = await self.sock.recv()
            print(self.id + " > " + data)
            return json.loads(data)
        except ConnectionClosed:
            if not self.game is None:
                await self.game.kick_player(self)
            return None

class Game:
    def __init__(self, id):
        self.id = id
        self.players = []
        self.state = 'lobby'
        self.answers = {}

    async def req_question(self):
        qmaster = random.choice(self.players)
        questions = get_question_selection()
        await send_msg(qmaster, self, 'q_pick', questions)

    async def start(self):
        if self.state == 'lobby':
            self.state = 'get_question'
            await send_all(self, 'started')
            # one random player chooses a question
            await self.req_question()
            return True
        else:
            return False

    def add_player(self, player):
        if self.state == 'lobby':
            self.players.append(player)
            player.game = self
            return True
        else:
            return False

    async def kick_player(self, player):
        for p in self.players:
            if p == player or p.id == player or p.sock == player:
                await p.kick()
                self.players.remove(p)
                break

    async def ask_question(self, qmaster, question):
        if self.state == 'get_question':
            self.state = 'ask_question'
            self.answers = { qmaster.id : question }
            await send_all_except(qmaster, self, 'a_question', question)
            return True
        else:
            return False

    async def receive_answer(self, player, answer):
        if self.state == 'ask_question':
            if player.id in self.answers:
                return False

            self.answers[player.id] = answer

            if len(self.answers) == len(self.players):
                self.state = 'get_question'
                await send_all(self, 'a_question', self.answers)
                await self.req_question()

            return True
        else:
            return False

class GameDB:
    def __init__(self):
        self.contents = {}

    def __getitem__(self, id):
        if not id in self.contents:
            self.contents[id] = Game(id)
        return self.contents[id]

def make_message(game, type, content):
    return json.dumps({'game_id': game.id, 'type': type, 'content': content})

def get_number(path, socket):
    lis = currently_active[path]['players']
    return lis.index(socket) + 1

## All games as indexed by game-id
games = GameDB()

async def send_msg(player, game, type, content=''):
    out = make_message(game, type, content)
    print(player.id + " < " + out)
    await player.send(out)

async def send_err(player, game, content=''):
    await send_msg(player, game, 'error', content)

async def send_all(game, type, content=''):
    for player in game.players:
        await send_msg(player, game, type, content)

async def send_all_except(except_player, game, type, content=''):
    for player in game.players:
        if not player == except_player:
            await send_msg(player, game, type, content)

async def register_player(player, game):
    if game.add_player(player):
        await send_msg(player, game, 'registered', '')
    else:
        await send_err(player, game, 'could not register')

async def start_game(game):
    if not await game.start():
        # ignore additional start requests
        None

async def kick_player(player, game):
    await game.kick_player(player)

async def ask_question(player, game, question):
    if not await game.ask_question(player, question):
        await send_err(player, game, 'could not post question')

async def receive_answer(player, game, answer):
    if not await game.receive_answer(player, answer):
        await send_err(player, game, 'could not post answer')

async def user_connect(websocket, user_id):
    print(user_id + " +")
    player = Player(user_id, websocket)

    while True:
        data = await player.receive()

        if data is None:
            break

        type = data['type']
        game_id = data['game_id']
        game = games[game_id]
        content = data['content']

        if type == "register":
            await register_player(player, game)

        elif type == 'start':
            await start_game(game)

        elif type == "quit":
            await kick_player(player, game)

        elif type == "p_question":
            await ask_question(player, game, content)

        elif type == "answer":
            await receive_answer(player, game, content)

        elif type == "echo":
            await send_msg(player, game, 'echo', data)

        else:
            await send_err(player, game, 'unrecognised message type: ' + type)

start_server = websockets.serve(user_connect, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
