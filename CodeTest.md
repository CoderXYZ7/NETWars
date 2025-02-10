```python
# server.py
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn

class User:
    def __init__(self, username, websocket):
        self.username = username
        self.websocket = websocket
        self.board = self.create_board()
        self.opponent = None

    def create_board(self):
        return [[0 for _ in range(10)] for _ in range(10)]

class GameManager:
    def __init__(self):
        self.waiting_player = None
        self.active_games = {}

    async def connect(self, username: str, websocket: WebSocket):
        user = User(username, websocket)
        
        if self.waiting_player:
            # Match found
            user.opponent = self.waiting_player
            self.waiting_player.opponent = user
            
            # Remove from waiting
            waiting_username = self.waiting_player.username
            self.active_games[frozenset([username, waiting_username])] = (user, self.waiting_player)
            self.waiting_player = None
            
            # Notify both players
            await user.websocket.send_json({
                "type": "game_start", 
                "opponent": waiting_username,
                "turn": random.choice([username, waiting_username])
            })
            await user.opponent.websocket.send_json({
                "type": "game_start", 
                "opponent": username,
                "turn": random.choice([username, waiting_username])
            })
        else:
            # No waiting player, add to queue
            self.waiting_player = user
            await websocket.send_json({"type": "waiting"})

    async def disconnect(self, username: str):
        # Handle game termination if opponent exists
        game_key = next((k for k in self.active_games.keys() if username in k), None)
        if game_key:
            game = self.active_games[game_key]
            for player in game:
                if player.username != username:
                    await player.websocket.send_json({"type": "opponent_disconnected"})
            del self.active_games[game_key]

    async def handle_attack(self, username: str, data: dict):
        game_key = next(k for k in self.active_games.keys() if username in k)
        game = self.active_games[game_key]
        
        # Find attacker and defender
        attacker = next(p for p in game if p.username == username)
        defender = next(p for p in game if p.username != username)
        
        x, y = data['x'], data['y']
        hit = defender.board[y][x] == 1
        
        # Send attack result to both players
        await attacker.websocket.send_json({
            "type": "attack_result",
            "x": x, 
            "y": y, 
            "hit": hit
        })
        await defender.websocket.send_json({
            "type": "under_attack",
            "x": x, 
            "y": y, 
            "hit": hit
        })

app = FastAPI()
game_manager = GameManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    try:
        await game_manager.connect(username, websocket)
        
        while True:
            data = await websocket.receive_json()
            
            if data['type'] == 'attack':
                await game_manager.handle_attack(username, data)
            
    except WebSocketDisconnect:
        await game_manager.disconnect(username)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# client.py
import asyncio
import websockets
import json
import random

class WarshipClient:
    def __init__(self, username):
        self.username = username
        self.websocket = None
        self.board = [[0 for _ in range(10)] for _ in range(10)]
        self.opponent = None
        self.is_my_turn = False

    async def connect(self):
        self.websocket = await websockets.connect(f"ws://localhost:8000/ws/{self.username}")
        await self.listen()

    async def listen(self):
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'waiting':
                    print("Waiting for an opponent...")
                
                elif data['type'] == 'game_start':
                    self.opponent = data['opponent']
                    self.is_my_turn = data['turn'] == self.username
                    print(f"Game started with {self.opponent}")
                    print(f"{'Your' if self.is_my_turn else 'Opponent\'s'} turn")
                
                elif data['type'] == 'attack_result':
                    print(f"Attack at ({data['x']}, {data['y']}) - {'Hit' if data['hit'] else 'Miss'}")
                
                elif data['type'] == 'under_attack':
                    print(f"Attacked at ({data['x']}, {data['y']}) - {'Hit' if data['hit'] else 'Miss'}")
                
                elif data['type'] == 'opponent_disconnected':
                    print("Opponent disconnected")
                    break

    async def attack(self, x, y):
        if self.is_my_turn and self.websocket:
            await self.websocket.send(json.dumps({
                "type": "attack",
                "x": x,
                "y": y
            }))
            self.is_my_turn = False

async def main():
    username = input("Enter your username: ")
    client = WarshipClient(username)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())

# requirements.txt
fastapi==0.95.1
uvicorn==0.22.0
websockets==11.0.3
pydantic==1.10.7
```
