#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import random
from websockets.exceptions import ConnectionClosed

import pickle

infile = open("../save_file.pkl",'rb')
reddit_file = pickle.load(infile)
infile.close()

def get_question_selection():
    ret = []
    for i in range(0,3):
        ret.append(random.choice(list(reddit_file.keys())))
    return ret

class Player:
    def __init__(self, game, sock):
        self.sock = sock
        self.id = ''
        self.game = game

    def kick(self):
        self.sock.close()

    async def send(self, msg):
        await self.sock.send(msg)

    async def receive(self):
        try:
    def __init__(self, game, sock):
        self.sock = sock
        self.id = ''
        self.game = game

    def kick(self):
        self.sock.close()

    async def send(self, msg):
        await self.sock.send(msg)

    async def receive(self):
        try:
            data = await self.sock.recv()
            print(self.game.id + "/" + self.id + " > " + data)
            return json.loads(data)
        except ConnectionClosed:
            if not self.game is None:
                await self.game.kick_player(self)
            return None
            data = await self.sock.recv()
            print(self.game.id + "/" + self.id + " > " + data)
            return json.loads(data)
        except ConnectionClosed:
            if not self.game is None:
                await self.game.kick_player(self)
            return None

class RobotPlayer:
    def __init__(self, game, sock):
        self.sock = ""
        self.id = ''
        self.game = game

    def kick(self):
        return

    async def send(self, msg):
        return

    async def receive(self):
        return

class Game:
    def __init__(self, id):
        self.id = id
        self.players = []
        self.state = 'lobby'
        self.answers = {}
        self.names = [ '1', '2', '3', 'b', 'c', 'tango', 'wowzer', 'bobbo', 'howdy' ]
        self.robot_man = RobotPlayer("", "")
        self.players.append(self.robot_man)
        self.robot_man.id = self.get_name()

    async def req_question(self):
        lesser_list = self.players
        if self.robot_man in lesser_list:
            lesser_list.remove(self.robot_man)
        qmaster = random.choice(lesser_list)
        questions = get_question_selection()
        await send_msg(qmaster, self, 'q_pick', questions)

    async def start(self):
        if self.state == 'lobby':
            self.state = 'get_question'
            content = map(lambda p: p.id, self.players)
            await send_all(self, 'started', list(content))
            # one random player chooses a question
            await self.req_question()
            return True
        else:
            return False

    def get_name(self):
        result = random.choice(self.names)
        self.names.remove(result)
        return result

    def return_name(self, name):
        self.names.append(name)

    def add_player(self, player):
        if self.state == 'lobby':
            self.players.append(player)
            player.id = self.get_name()
            return True
        else:
            return False

    async def kick_player(self, player):
        for p in self.players:
            if p.sock is None:
                self.players.remove(p)
                self.return_name(p.id)
            elif p == player or p.id == player or p.sock == player:
                await p.kick()
                self.players.remove(p)
                self.return_name(p.id)
                break


    async def ask_question(self, qmaster, question):
        if self.state == 'get_question':
            self.state = 'ask_question'
            self.answers = { qmaster.id : question }
            await send_all_except(qmaster, self, 'a_question', question)
            self.answers[self.robot_man.id] = reddit_file[question][0]
            return True
        else:
            return False

    async def receive_answer(self, player, answer):
        if self.state == 'ask_question':
            if player.id in self.answers:
                return False

            self.answers[player.id] = answer

            if len(self.answers) == 1 + len(self.players):
                self.state = 'get_question'
                await send_all(self, 'answer', self.answers)
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

def make_message(player, game, type, content):
    return json.dumps({
        'user_id': player.id,
        'game_id': game.id,
        'type': type,
        'content': content
    })

def get_number(path, socket):
    lis = currently_active[path]['players']
    return lis.index(socket) + 1

## All games as indexed by game-id
games = GameDB()

async def send_msg(player, game, type, content=''):
    out = make_message(player, game, type, content)
    print(game.id + "/" + player.id + " < " + out)
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

async def guess(player, game, data):
    if data.content = game.robot_man.robot_id:
        # Correct guess
        for p in game.players:
            await send_msg(p,game, "game_won", p.id)
        # end the game
        game.remove(game)
    else:
        await send_msg(player, "game_over", "You're Out")
        await game.kick_player(player)

async def user_connect(websocket, game_id):
    print(game_id + " +")
    game = games[game_id]
    player = Player(game, websocket)

    while True:
        data = await player.receive()

        if data is None:
            break

        type = data['type']
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

        elif type == "guess"
            await guess(player, game, data)

        else:
            await send_err(player, game, 'unrecognised message type: ' + type)

start_server = websockets.serve(user_connect, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
