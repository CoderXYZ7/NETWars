import sys
import json
import socket
import random
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QMessageBox, QRadioButton, QButtonGroup, QFrame, QLineEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from functools import partial

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Generate a random ID for client instance
CLIENT_ID = random.randint(1, 1000000)

class NetworkThread(QThread):
    data_received = pyqtSignal(dict)
    connection_lost = pyqtSignal()

    def __init__(self, client_socket):
        super().__init__()
        self.client = client_socket
        self.running = True

    def run(self):
        buffer = ""
        while self.running:
            try:
                data = self.client.recv(4096).decode('utf-8')
                if not data:
                    logger.warning(f"Client {CLIENT_ID}: No data received from server. Connection may be closed.")
                    self.connection_lost.emit()
                    break
                
                buffer += data
                logger.debug(f"Client {CLIENT_ID}: Received raw data: {data}")
                
                # Process complete JSON messages from buffer
                while '{' in buffer and '}' in buffer:
                    try:
                        # Find the position of the first JSON object
                        start = buffer.find('{')
                        end = buffer.find('}', start) + 2
                        
                        # Extract the complete JSON message
                        json_str = buffer[start:end]
                        # Remove the processed part from buffer
                        buffer = buffer[end:]
                        
                        # Parse and emit the message
                        message = json.loads(json_str)
                        logger.debug(f"Client {CLIENT_ID}: Processed message: {message}")
                        self.data_received.emit(message)
                    except json.JSONDecodeError as e:
                        logger.error(f"Client {CLIENT_ID}: JSON decode error: {e}")
                        logger.error(f"Client {CLIENT_ID}: Problematic JSON: {json_str}")
                        # Skip to the next opening brace
                        if '{' in buffer:
                            buffer = buffer[buffer.find('{'):]
                        else:
                            buffer = ""
                            break
            except ConnectionResetError:
                logger.error(f"Client {CLIENT_ID}: Connection reset by server")
                self.connection_lost.emit()
                break
            except ConnectionAbortedError:
                logger.error(f"Client {CLIENT_ID}: Connection aborted")
                self.connection_lost.emit()
                break
            except Exception as e:
                logger.error(f"Client {CLIENT_ID}: Network error: {str(e)}")
                self.connection_lost.emit()
                break
        
        logger.debug(f"Client {CLIENT_ID}: Network thread stopping")

    def stop(self):
        self.running = False

class BattleshipClient(QMainWindow):
    def __init__(self):
        super().__init__()
        # Game state
        self.username = None
        self.connected = False
        self.placement_mode = True
        self.current_turn = False
        self.game_over = False
        self.attacks_disabled = False
        self.orientation = "horizontal"
        
        # Board and ships
        self.board_size = 10
        self.grid = [[0] * self.board_size for _ in range(self.board_size)]
        self.enemy_grid = [[0] * self.board_size for _ in range(self.board_size)]
        self.ships_to_place = [5, 4, 3, 3, 2]  # Ship lengths
        self.placed_ships = []
        self.attacked_coords = set()
        
        # Cards
        self.hand = []
        self.selected_card = None
        
        # Network
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.network_thread = None
        
        # Initialize UI
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Battleship - Connect")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow { background-color: #2E3440; }
            QLabel, QRadioButton, QGroupBox { color: #D8DEE9; }
            QPushButton { 
                background-color: #4C566A; 
                color: #ECEFF4; 
                border: 1px solid #81A1C1; 
                padding: 5px; 
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #5E81AC; }
            QPushButton:disabled { background-color: #434C5E; color: #677691; }
            QLineEdit { 
                background-color: #3B4252; 
                color: #E5E9F0; 
                border: 1px solid #81A1C1; 
                padding: 5px; 
                border-radius: 3px;
            }
        """)

        central = QWidget()
        layout = QVBoxLayout()

        # Username input
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setStyleSheet("font-size: 14px;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Connect button
        self.connect_btn = QPushButton("Connect to Server")
        self.connect_btn.setStyleSheet("background-color: #81A1C1; color: #2E3440; font-weight: bold; padding: 8px;")
        self.connect_btn.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_btn)

        # Status label
        self.status_label = QLabel("Enter your username and connect to start the game.")
        self.status_label.setStyleSheet("font-size: 14px; margin-top: 10px; margin-bottom: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def connect_to_server(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Please enter a username.")
            return

        self.username = username
        self.connect_btn.setEnabled(False)
        self.status_label.setText("Connecting to server...")

        try:
            logger.info(f"Client {CLIENT_ID}: Connecting to server as '{username}'...")
            self.client.connect(('localhost', 5555))
            self.client.send(username.encode('utf-8'))
            self.connected = True
            
            # Start network thread
            self.network_thread = NetworkThread(self.client)
            self.network_thread.data_received.connect(self.handle_message)
            self.network_thread.connection_lost.connect(self.handle_disconnect)
            self.network_thread.start()
            
            logger.info(f"Client {CLIENT_ID}: Connected successfully as '{username}'")
            self.setup_game_ui()
        except ConnectionRefusedError:
            logger.error(f"Client {CLIENT_ID}: Connection refused. Server may be down.")
            QMessageBox.critical(self, "Connection Error", "Could not connect to server. Server may be down.")
            self.connect_btn.setEnabled(True)
            self.status_label.setText("Connection failed. Please try again.")
        except Exception as e:
            logger.error(f"Client {CLIENT_ID}: Connection error: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"An error occurred: {str(e)}")
            self.connect_btn.setEnabled(True)
            self.status_label.setText("Connection failed. Please try again.")

    def setup_game_ui(self):
        self.setWindowTitle(f"Battleship - {self.username}")
        
        central = QWidget()
        main_layout = QVBoxLayout()

        # Status area at top
        self.status_label = QLabel(f"Welcome, {self.username}! Place your ships.")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #88C0D0; margin: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Ship placement controls
        self.setup_placement_controls(main_layout)
        
        # Game boards
        boards_layout = QHBoxLayout()
        boards_layout.addWidget(self.create_player_board())
        boards_layout.addWidget(self.create_enemy_board())
        main_layout.addLayout(boards_layout)
        
        # Card display
        self.card_frame = QGroupBox("Your Cards")
        self.card_frame.setStyleSheet("QGroupBox { font-size: 14px; border: 1px solid #81A1C1; margin-top: 10px; padding-top: 20px; }")
        self.card_layout = QHBoxLayout()
        self.card_frame.setLayout(self.card_layout)
        main_layout.addWidget(self.card_frame)
        
        # Game controls
        control_layout = QHBoxLayout()
        
        # Draw card button
        self.draw_btn = QPushButton("Draw Card")
        self.draw_btn.setStyleSheet("background-color: #81A1C1; color: #2E3440; font-weight: bold; padding: 10px;")
        self.draw_btn.clicked.connect(self.draw_card)
        self.draw_btn.setEnabled(False)
        control_layout.addWidget(self.draw_btn)
        
        main_layout.addLayout(control_layout)
        
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def setup_placement_controls(self, layout):
        self.orientation_frame = QGroupBox("Ship Orientation")
        self.orientation_frame.setStyleSheet("QGroupBox { font-size: 14px; border: 1px solid #81A1C1; margin-top: 10px; padding-top: 20px; }")
        
        orientation_layout = QHBoxLayout()
        self.horizontal_radio = QRadioButton("Horizontal")
        self.vertical_radio = QRadioButton("Vertical")
        self.horizontal_radio.setChecked(True)
        
        self.horizontal_radio.toggled.connect(lambda: self.set_orientation("horizontal"))
        self.vertical_radio.toggled.connect(lambda: self.set_orientation("vertical"))
        
        orientation_layout.addWidget(self.horizontal_radio)
        orientation_layout.addWidget(self.vertical_radio)
        
        ship_info = QLabel(f"Place {self.ships_to_place[0]}-unit ship")
        ship_info.setAlignment(Qt.AlignCenter)
        orientation_layout.addWidget(ship_info)
        
        self.orientation_frame.setLayout(orientation_layout)
        layout.addWidget(self.orientation_frame)

    def create_player_board(self):
        self.player_board = QGroupBox("Your Fleet")
        self.player_board.setStyleSheet("QGroupBox { font-size: 14px; border: 1px solid #81A1C1; margin-top: 10px; padding-top: 20px; }")
        
        player_layout = QVBoxLayout()
        self.player_grid_layout = QGridLayout()
        self.player_grid_layout.setSpacing(2)
        
        # Create grid labels
        for i in range(10):
            # Row labels (A-J)
            row_label = QLabel(chr(65 + i))
            row_label.setAlignment(Qt.AlignCenter)
            self.player_grid_layout.addWidget(row_label, i+1, 0)
            
            # Column labels (1-10)
            col_label = QLabel(str(i+1))
            col_label.setAlignment(Qt.AlignCenter)
            self.player_grid_layout.addWidget(col_label, 0, i+1)
        
        # Create grid buttons
        self.player_buttons = [[QPushButton() for _ in range(10)] for _ in range(10)]
        for row in range(10):
            for col in range(10):
                btn = self.player_buttons[row][col]
                btn.setFixedSize(35, 35)
                btn.setStyleSheet("background-color: #4C566A; border: 1px solid #81A1C1;")
                btn.clicked.connect(partial(self.handle_placement_click, row, col))
                self.player_grid_layout.addWidget(btn, row+1, col+1)
        
        player_layout.addLayout(self.player_grid_layout)
        self.player_board.setLayout(player_layout)
        return self.player_board

    def create_enemy_board(self):
        self.enemy_board = QGroupBox("Enemy Waters")
        self.enemy_board.setStyleSheet("QGroupBox { font-size: 14px; border: 1px solid #81A1C1; margin-top: 10px; padding-top: 20px; }")
        
        enemy_layout = QVBoxLayout()
        self.enemy_grid_layout = QGridLayout()
        self.enemy_grid_layout.setSpacing(2)
        
        # Create grid labels
        for i in range(10):
            # Row labels (A-J)
            row_label = QLabel(chr(65 + i))
            row_label.setAlignment(Qt.AlignCenter)
            self.enemy_grid_layout.addWidget(row_label, i+1, 0)
            
            # Column labels (1-10)
            col_label = QLabel(str(i+1))
            col_label.setAlignment(Qt.AlignCenter)
            self.enemy_grid_layout.addWidget(col_label, 0, i+1)
        
        # Create grid buttons
        self.enemy_buttons = [[QPushButton() for _ in range(10)] for _ in range(10)]
        for row in range(10):
            for col in range(10):
                btn = self.enemy_buttons[row][col]
                btn.setFixedSize(35, 35)
                btn.setStyleSheet("background-color: #4C566A; border: 1px solid #81A1C1;")
                btn.clicked.connect(partial(self.handle_attack_click, row, col))
                btn.setEnabled(False)  # Disable until game starts
                self.enemy_grid_layout.addWidget(btn, row+1, col+1)
        
        enemy_layout.addLayout(self.enemy_grid_layout)
        self.enemy_board.setLayout(enemy_layout)
        return self.enemy_board

    def set_orientation(self, orientation):
        self.orientation = orientation
        logger.debug(f"Client {CLIENT_ID}: Ship orientation set to {orientation}")

    def handle_placement_click(self, row, col):
        if not self.placement_mode or not self.ships_to_place:
            return
        
        logger.debug(f"Client {CLIENT_ID}: Placement click at ({row}, {col}) with orientation {self.orientation}")
        
        ship_length = self.ships_to_place[0]
        ship_coords = []
        
        try:
            # Check if ship placement is valid
            if self.orientation == "horizontal":
                if col + ship_length > 10:
                    raise ValueError(f"Ship extends beyond the right edge of the board")
                
                for c in range(col, col + ship_length):
                    if self.grid[row][c] == 1:
                        raise ValueError(f"Ship overlaps with existing ship at ({row}, {c})")
                    ship_coords.append((row, c))
            else:  # vertical
                if row + ship_length > 10:
                    raise ValueError(f"Ship extends beyond the bottom edge of the board")
                
                for r in range(row, row + ship_length):
                    if self.grid[r][col] == 1:
                        raise ValueError(f"Ship overlaps with existing ship at ({r}, {col})")
                    ship_coords.append((r, col))
            
            # Place the ship
            for r, c in ship_coords:
                self.grid[r][c] = 1
                self.player_buttons[r][c].setStyleSheet("background-color: #88C0D0; border: 1px solid #81A1C1;")
            
            self.placed_ships.append(ship_coords)
            self.ships_to_place.pop(0)
            
            if not self.ships_to_place:
                self.finish_placement()
            else:
                # Update status for next ship
                self.status_label.setText(f"Place {self.ships_to_place[0]}-unit ship")
                # Also update the orientation frame label
                for i in range(self.orientation_frame.layout().count()):
                    widget = self.orientation_frame.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel):
                        widget.setText(f"Place {self.ships_to_place[0]}-unit ship")
            
        except ValueError as e:
            logger.warning(f"Client {CLIENT_ID}: Invalid ship placement: {str(e)}")
            QMessageBox.warning(self, "Invalid Placement", str(e))

    def finish_placement(self):
        logger.info(f"Client {CLIENT_ID}: All ships placed, finishing placement phase")
        self.placement_mode = False
        self.orientation_frame.hide()
        self.status_label.setText("Waiting for opponent...")
        
        # Format ship data for server
        ships_data = []
        for ship in self.placed_ships:
            ship_data = []
            for r, c in ship:
                ship_data.append([r, c])
            ships_data.append(ship_data)
        
        # Send placement data to server
        placement_msg = {
            'type': 'placement',
            'ships': ships_data
        }
        logger.debug(f"Client {CLIENT_ID}: Sending placement data: {placement_msg}")
        self.send_message(placement_msg)

    def handle_attack_click(self, row, col):
        logger.debug(f"Client {CLIENT_ID}: Attack click at ({row}, {col}). Current turn: {self.current_turn}, Attacks disabled: {self.attacks_disabled}")
        
        # Check if attack is valid
        if not self.current_turn:
            self.status_label.setText("Not your turn!")
            return
        
        if self.game_over:
            self.status_label.setText("Game is over!")
            return
        
        if self.attacks_disabled:
            self.status_label.setText("Your attacks are disabled this turn!")
            return
        
        if (row, col) in self.attacked_coords:
            self.status_label.setText("You've already attacked this position!")
            return
        
        if not self.selected_card:
            self.status_label.setText("Select a card before attacking!")
            return
        
        # Track attacked coordinate
        self.attacked_coords.add((row, col))
        
        # Send attack to server
        attack_msg = {
            'type': 'attack',
            'card': self.selected_card,
            'row': row,
            'col': col
        }
        logger.debug(f"Client {CLIENT_ID}: Sending attack: {attack_msg}")
        self.send_message(attack_msg)
        
        # Update UI
        self.status_label.setText(f"Attack sent to ({row}, {col}) with {self.selected_card['name']}")
        
        # Clear selected card
        self.selected_card = None
        self.update_card_buttons()
        
        # Disable further attacks until next turn
        self.current_turn = False
        self.update_board_states()

    def draw_card(self):
        if not self.current_turn or self.game_over:
            return
        
        logger.debug(f"Client {CLIENT_ID}: Drawing card")
        self.send_message({'type': 'draw_card'})
        self.draw_btn.setEnabled(False)  # Prevent multiple draws

    def select_card(self, card):
        if not self.current_turn or self.game_over or self.attacks_disabled:
            return
        
        logger.debug(f"Client {CLIENT_ID}: Selected card: {card['name']}")
        self.selected_card = card
        self.update_card_buttons()
        self.status_label.setText(f"Selected {card['name']} - Choose target")

    def update_card_buttons(self):
        # Remove existing card buttons
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create new card buttons
        if not self.hand:
            empty_label = QLabel("No cards in hand")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #D8DEE9;")
            self.card_layout.addWidget(empty_label)
            return
        
        for card in self.hand:
            card_btn = QPushButton()
            card_btn.setFixedWidth(120)
            
            # Set card text with name and description
            card_text = f"{card['name']}\n{card['description']}"
            card_btn.setText(card_text)
            
            # Style based on selection
            if card == self.selected_card:
                card_btn.setStyleSheet("""
                    background-color: #5E81AC;
                    color: #ECEFF4;
                    border: 2px solid #88C0D0;
                    padding: 5px;
                    text-align: center;
                """)
            else:
                card_btn.setStyleSheet("""
                    background-color: #4C566A;
                    color: #E5E9F0;
                    border: 1px solid #81A1C1;
                    padding: 5px;
                    text-align: center;
                """)
            
            card_btn.clicked.connect(partial(self.select_card, card))
            self.card_layout.addWidget(card_btn)

    def handle_message(self, data):
        if not data or 'type' not in data:
            logger.warning(f"Client {CLIENT_ID}: Received invalid message format: {data}")
            return
        
        msg_type = data['type']
        logger.debug(f"Client {CLIENT_ID}: Handling message type: {msg_type}")
        
        if msg_type == 'game_start':
            self.handle_game_start(data)
        elif msg_type == 'turn_update':
            self.handle_turn_update(data)
        elif msg_type == 'new_card':
            self.handle_new_card(data)
        elif msg_type == 'attack_result':
            self.handle_attack_result(data)
        elif msg_type == 'game_over':
            self.handle_game_over(data)
        else:
            logger.warning(f"Client {CLIENT_ID}: Unknown message type: {msg_type}")

    def handle_game_start(self, data):
        logger.info(f"Client {CLIENT_ID}: Game started")
        self.current_turn = (data['current_player'] == self.username)
        self.draw_btn.setEnabled(True)
        
        if self.current_turn:
            self.status_label.setText("Game started! It's your turn.")
        else:
            self.status_label.setText("Game started! Waiting for opponent's move.")
        
        self.update_board_states()

    def handle_turn_update(self, data):
        logger.debug(f"Client {CLIENT_ID}: Turn update - current player: {data['current_player']}")
        self.current_turn = (data['current_player'] == self.username)
        self.attacks_disabled = False
        self.draw_btn.setEnabled(self.current_turn)
        
        if self.current_turn:
            self.status_label.setText("It's your turn!")
        else:
            self.status_label.setText("Opponent's turn...")
        
        self.update_board_states()

    def handle_new_card(self, data):
        card = data['card']
        logger.debug(f"Client {CLIENT_ID}: Received new card: {card['name']}")
        self.hand.append(card)
        self.update_card_buttons()
        self.status_label.setText(f"Drew card: {card['name']}")

    def handle_attack_result(self, data):
        logger.debug(f"Client {CLIENT_ID}: Attack result - Player: {data['player']}, Coords: {data['coords']}, Hits: {data['hits']}")
        
        # Process special effects first
        if 'special_effect' in data and data['special_effect']:
            self.handle_special_effect(data['special_effect'], data)
        
        # Update appropriate grid based on who made the attack
        if data['player'] == self.username:  # I attacked
            for coord, hit in zip(data['coords'], data['hits']):
                row, col = coord
                color = "#BF616A" if hit else "#D8DEE9"  # Red for hit, white for miss
                self.enemy_buttons[row][col].setStyleSheet(f"background-color: {color}; border: 1px solid #81A1C1;")
                self.enemy_buttons[row][col].setText("HIT" if hit else "MISS")  # Add text feedback
        else:  # I was attacked
            for coord, hit in zip(data['coords'], data['hits']):
                row, col = coord
                if hit:
                    self.player_buttons[row][col].setStyleSheet("background-color: #BF616A; border: 1px solid #81A1C1;")  # Red for hit
                    self.player_buttons[row][col].setText("HIT")  # Add text feedback
                else:
                    self.player_buttons[row][col].setStyleSheet("background-color: #D8DEE9; border: 1px solid #81A1C1;")  # White for miss
                    self.player_buttons[row][col].setText("MISS")  # Add text feedback

    def handle_special_effect(self, effect, data):
        logger.debug(f"Client {CLIENT_ID}: Handling special effect: {effect}")
        
        # Remove the special card if it was used
        if effect != 'single':
            self.hand = [c for c in self.hand if c['name'] != effect]
            self.update_card_buttons()
        
        # Handle specific effects
        if effect == 'EMP':
            if data['player'] != self.username:  # If opponent used EMP on me
                self.attacks_disabled = True
                self.status_label.setText("Your attacks are disabled for this turn!")
                QMessageBox.information(self, "EMP Attack", "Your systems are disabled for this turn!")
        
        # Sonar or recon reveals
        elif effect in ['sonar', 'recon']:
            if data['player'] == self.username:  # If I used sonar/recon
                for coord in data.get('coords', []):
                    r, c = coord
                    if self.enemy_grid[r][c] == 0:  # Only update cells that aren't already hit/missed
                        self.enemy_buttons[r][c].setStyleSheet("background-color: #7B88A1; border: 1px solid #81A1C1;")  # Light gray for scanned

    def handle_game_over(self, data):
        logger.info(f"Client {CLIENT_ID}: Game over - {data['message']}")
        self.game_over = True
        self.current_turn = False
        self.update_board_states()
        
        # Show game over message
        QMessageBox.information(self, "Game Over", data['message'])
        
        # Update status
        self.status_label.setText(f"Game Over! {data['message']}")
        
        # Disable draw button
        self.draw_btn.setEnabled(False)

    def handle_disconnect(self):
        if self.connected:
            logger.warning(f"Client {CLIENT_ID}: Connection to server lost")
            self.connected = False
            QMessageBox.critical(self, "Connection Lost", "Connection to the server has been lost.")
            self.close()

    def update_board_states(self):
        # Enable/disable enemy board based on turn
        for row in range(10):
            for col in range(10):
                btn = self.enemy_buttons[row][col]
                # Only enable buttons for positions not already attacked and when it's our turn
                can_attack = (self.current_turn and 
                              not self.game_over and 
                              not self.attacks_disabled and 
                              (row, col) not in self.attacked_coords)
                btn.setEnabled(can_attack)
        
        # Update draw button state
        self.draw_btn.setEnabled(self.current_turn and not self.game_over)

    def send_message(self, message):
        try:
            if self.connected:
                # Ensure the message is properly serialized to JSON
                json_message = json.dumps(message, ensure_ascii=False)
                logger.debug(f"Client {CLIENT_ID}: Sending message: {json_message}")
                self.client.send(json_message.encode('utf-8'))
            else:
                logger.warning(f"Client {CLIENT_ID}: Cannot send message - not connected")
        except json.JSONDecodeError as e:
            logger.error(f"Client {CLIENT_ID}: JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Client {CLIENT_ID}: Error sending message: {str(e)}")
            self.handle_disconnect()

    def closeEvent(self, event):
        logger.info(f"Client {CLIENT_ID}: Closing application")
        if self.network_thread and self.network_thread.isRunning():
            self.network_thread.stop()
            self.network_thread.wait(1000)  # Wait up to 1 second for thread to finish
        
        if self.connected and self.client:
            try:
                self.client.close()
            except:
                pass
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BattleshipClient()
    window.show()
    sys.exit(app.exec_())