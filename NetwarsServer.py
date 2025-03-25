import socket
import threading
import random
import json
from collections import defaultdict
import time
import argparse  # Added for command-line argument parsing

class GameState:
    def __init__(self, player1, player2):
        self.players = [player1, player2]
        self.ships = {player1: [], player2: []}  # Stores ships for each player
        self.hands = {player1: [], player2: []}  # Stores cards for each player
        self.current_turn = None  # Tracks whose turn it is
        self.revealed_cells = defaultdict(set)  # Tracks revealed cells (for Recon/Sonar)
        self.attacked_coords = defaultdict(set)  # Tracks all attacks made by each player
        self.card_pool = self.init_cards()  # Initializes the pool of available cards
        self.disconnected_players = set()  # Tracks disconnected players
        self.last_action_time = time.time()  # Tracks the last action time for reconnection

    def init_cards(self):
        """Initialize the pool of cards with their effects."""
        return [
            {'name': 'Standard', 'description': 'Basic attack', 'effect': 'single'},
            {'name': 'Vertical', 'description': '3 vertical cells', 'effect': 'vertical'},
            {'name': 'Horizontal', 'description': '3 horizontal cells', 'effect': 'horizontal'},
            {'name': 'Bombardment', 'description': '2x2 area', 'effect': 'bombardment'},  # Reduced area
            {'name': 'Recon Drone', 'description': 'Reveal 3x3 area (2 uses)', 'effect': 'recon', 'uses': 2},
            {'name': 'Sonar Ping', 'description': 'Detect in 5x5 area (1 use)', 'effect': 'sonar', 'uses': 1},
            {'name': 'EMP', 'description': 'Disable enemy attacks for one turn (also disables your next attack)', 'effect': 'EMP'}
        ]

    def get_random_card(self):
        """Draw a random card from the card pool."""
        return random.choice(self.card_pool)

    def validate_ships(self, username, ships):
        """Validate the ship placements for a player."""
        required_lengths = [5, 4, 3, 3, 2]  # Required ship lengths
        placed_coords = set()  # Tracks all coordinates occupied by ships

        if len(ships) != len(required_lengths):
            return False  # Incorrect number of ships

        for i, ship in enumerate(ships):
            if len(ship) != required_lengths[i]:
                return False  # Ship length mismatch
            for coord in ship:
                x, y = coord
                if not (0 <= x < 10 and 0 <= y < 10):
                    return False  # Ship out of bounds
                if tuple(coord) in placed_coords:
                    return False  # Overlapping ships
                placed_coords.add(tuple(coord))
        return True

class BattleshipServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(2)  # Allow up to 2 players

        self.clients = []  # Stores connected clients
        self.usernames = []  # Stores usernames of connected players
        self.game_state = None  # Tracks the game state
        self.lock = threading.Lock()  # Ensures thread-safe operations
        self.reconnect_timeout = 60  # Timeout for reconnection in seconds

    def handle_client(self, client, username):
        """Handle communication with a connected client."""
        try:
            buffer = ""
            while True:
                data = client.recv(4096).decode('utf-8')
                if not data:
                    break  # Client disconnected
                buffer += data

                # Process all complete JSON messages in the buffer
                while True:
                    start = buffer.find('{')
                    if start == -1:
                        break  # No JSON object starts
                    brace_count = 0
                    end = start
                    for i, c in enumerate(buffer[start:]):
                        if c == '{':
                            brace_count += 1
                        elif c == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = start + i + 1  # Include the closing brace
                                break
                    if brace_count != 0:
                        break  # Incomplete JSON object

                    msg_str = buffer[start:end]
                    buffer = buffer[end:]

                    try:
                        msg = json.loads(msg_str)
                        with self.lock:
                            self.process_message(username, msg)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error for {username}: {e}")
        except Exception as e:
            print(f"Connection error with {username}: {e}")
        finally:
            self.handle_disconnect(client, username)

    def process_message(self, username, msg):
        """Process incoming messages from clients."""
        if msg['type'] == 'placement':
            if self.game_state.validate_ships(username, msg['ships']):
                self.game_state.ships[username] = msg['ships']
                if all(len(v) > 0 for v in self.game_state.ships.values()):
                    self.start_game()  # Start the game if both players have placed ships
            else:
                self.send_to(username, {'type': 'invalid_placement'})

        elif msg['type'] == 'attack':
            self.process_attack(username, msg)

        elif msg['type'] == 'draw_card':
            self.handle_card_draw(username)

        elif msg['type'] == 'reconnect':
            self.handle_reconnect(username, msg)

    def start_game(self):
        """Start the game and notify both players."""
        first_player = random.choice(self.game_state.players)
        self.game_state.current_turn = first_player
        self.broadcast({
            'type': 'game_start',
            'current_player': first_player
        })

    def process_attack(self, attacker, msg):
        """Process an attack from a player."""
        defender = [p for p in self.game_state.players if p != attacker][0]
        row, col = msg['row'], msg['col']
        card = msg.get('card', {'effect': 'single'})

        # Validate the attack
        if not (self.game_state.current_turn == attacker and
                0 <= row < 10 and 0 <= col < 10 and
                (row, col) not in self.game_state.attacked_coords[attacker]):
            return

        # Remove the used card from the attacker's hand
        card_to_remove = None
        for c in self.game_state.hands[attacker]:
            if c['name'] == card['name']:
                card_to_remove = c
                break
        
        if card_to_remove:
            self.game_state.hands[attacker].remove(card_to_remove)
            # Notify client to remove the card from their hand
            self.send_to(attacker, {
                'type': 'remove_card',
                'card_name': card_to_remove['name']
            })

        # Calculate affected coordinates based on the card's effect
        coords = self.calculate_affected_coords(row, col, card['effect'])
        new_attacks = [(r, c) for r, c in coords 
                      if (r, c) not in self.game_state.attacked_coords[attacker]]

        # Check for hits
        hits = []
        for r, c in new_attacks:
            self.game_state.attacked_coords[attacker].add((r, c))
            hit = any([r, c] in ship for ship in self.game_state.ships[defender])
            hits.append(hit)
            if hit:
                for ship in self.game_state.ships[defender][:]:
                    if [r, c] in ship:
                        ship.remove([r, c])
                        if not ship:
                            self.game_state.ships[defender].remove(ship)

        # Check for win condition
        if not self.game_state.ships[defender]:
            self.broadcast({
                'type': 'game_over',
                'winner': attacker,
                'message': f"{attacker} destroyed all ships!"
            })
            return

        # Handle special effects
        if card['effect'] == 'recon':
            self.game_state.revealed_cells[defender].update(coords)
        elif card['effect'] == 'sonar':
            self.game_state.revealed_cells[defender].update(coords)
        elif card['effect'] == 'EMP':
            self.broadcast({
                'type': 'special_effect',
                'effect': 'EMP',
                'player': defender
            })

        # Update game state and notify players
        self.game_state.current_turn = defender
        self.broadcast({
            'type': 'attack_result',
            'player': attacker,
            'coords': new_attacks,
            'hits': hits,
            'special_effect': card['effect']
        })
        self.broadcast({
            'type': 'turn_update',
            'current_player': defender
        })

    def calculate_affected_coords(self, row, col, effect):
        """Calculate the coordinates affected by a card's effect."""
        if effect == 'single':
            return [(row, col)]
        elif effect == 'horizontal':
            return [(row, c) for c in range(max(0, col-1), min(10, col+2))]
        elif effect == 'vertical':
            return [(r, col) for r in range(max(0, row-1), min(10, row+2))]
        elif effect == 'bombardment':
            return [(r, c) for r in range(max(0, row-1), min(10, row+2)) 
                    for c in range(max(0, col-1), min(10, col+2))]
        elif effect == 'sonar':
            return [(r, c) for r in range(max(0, row-2), min(10, row+3))
                    for c in range(max(0, col-2), min(10, col+3))]
        elif effect == 'EMP':
            return [(row, col)]
        return [(row, col)]

    def handle_card_draw(self, username):
        """Handle a card draw request from a player."""
        if len(self.game_state.hands[username]) >= 5:
            return  # Hand limit reached
        card = self.game_state.get_random_card()
        self.game_state.hands[username].append(card)
        self.send_to(username, {
            'type': 'new_card',
            'card': card
        })
        # Disable further card draws for this turn
        self.send_to(username, {'type': 'disable_draw'})
        # Switch turn to the other player
        defender = [p for p in self.game_state.players if p != username][0]
        self.game_state.current_turn = defender
        self.broadcast({
            'type': 'turn_update',
            'current_player': defender
        })

    def handle_reconnect(self, username, msg):
        """Handle a reconnection request from a player."""
        if username in self.game_state.disconnected_players:
            self.game_state.disconnected_players.remove(username)
            self.broadcast({
                'type': 'reconnect_success',
                'username': username
            })
            # Send the current game state to the reconnected player
            self.send_to(username, {
                'type': 'game_state_update',
                'ships': self.game_state.ships[username],
                'hand': self.game_state.hands[username],
                'current_turn': self.game_state.current_turn
            })

    def handle_disconnect(self, client, username):
        """Handle a client disconnection."""
        with self.lock:
            if client in self.clients:
                index = self.clients.index(client)
                self.clients.pop(index)
                self.usernames.pop(index)
                print(f"{username} disconnected")
                client.close()

                if username in self.game_state.players:
                    self.game_state.disconnected_players.add(username)
                    # Start a timer for reconnection
                    threading.Timer(self.reconnect_timeout, self.handle_reconnect_timeout, args=[username]).start()

    def handle_reconnect_timeout(self, username):
        """Handle the reconnection timeout for a disconnected player."""
        if username in self.game_state.disconnected_players:
            self.game_state.disconnected_players.remove(username)
            self.broadcast({
                'type': 'game_over',
                'winner': [p for p in self.game_state.players if p != username][0],
                'message': f"{username} disconnected. Game over!"
            })

    def broadcast(self, message):
        """Send a message to all connected clients."""
        json_message = json.dumps(message) + "\n"  # Add newline delimiter
        for client in self.clients:
            try:
                client.send(json_message.encode('utf-8'))
            except:
                self.handle_disconnect(client, None)

    def send_to(self, username, message):
        """Send a message to a specific player."""
        if username in self.usernames:
            index = self.usernames.index(username)
            json_message = json.dumps(message) + "\n"  # Add newline delimiter
            self.clients[index].send(json_message.encode('utf-8'))

    def run(self):
        """Start the server and accept connections."""
        print(f"Server listening on port {self.port}...")
        while len(self.clients) < 2:
            client, addr = self.server.accept()
            username = client.recv(1024).decode('utf-8')
            print(f"{username} connected from {addr}")

            self.clients.append(client)
            self.usernames.append(username)

            if len(self.clients) == 2:
                self.game_state = GameState(*self.usernames)  # Initialize game state

            threading.Thread(target=self.handle_client, args=(client, username)).start()

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Battleship Game Server')
    parser.add_argument('-p', '--port', type=int, default=5555,
                       help='Port number to listen on (default: 5555)')
    
    args = parser.parse_args()
    
    # Start the server with the specified port
    server = BattleshipServer(port=args.port)
    server.run()