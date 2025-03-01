import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox, 
                             QRadioButton, QButtonGroup, QFrame, QScrollArea)
from PyQt5.QtCore import Qt
from functools import partial

class Card:
    def __init__(self, name, description, effect_function, special_type=None):
        self.name = name
        self.description = description
        self.effect_function = effect_function
        self.special_type = special_type  # For cards with special effects
    
    def use(self, game_board, row, col):
        return self.effect_function(game_board, row, col)

class BattleshipGame(QMainWindow):
    def __init__(self, player_name):
        super().__init__()
        self.player_name = player_name
        self.board_size = 10
        self.grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.enemy_grid = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.ships_to_place = [5, 4, 3, 3, 2]
        self.placed_ships = []
        self.placement_mode = True
        self.game_over = False
        
        # Card system
        self.hand_size = 5
        self.hand = []
        self.selected_card = None
        self.card_buttons = []
        
        # Special effect tracking
        self.attacks_disabled = False  # For EMP card
        self.revealed_cells = set()  # For Recon Drone and Sonar Ping
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"Battleship - {self.player_name} Ship Placement")
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Orientation selection
        orientation_layout = QHBoxLayout()
        self.horizontal_radio = QRadioButton("Horizontal")
        self.vertical_radio = QRadioButton("Vertical")
        self.horizontal_radio.setChecked(True)
        orientation_layout.addWidget(self.horizontal_radio)
        orientation_layout.addWidget(self.vertical_radio)
        main_layout.addLayout(orientation_layout)
        
        # Status label
        self.status_label = QLabel(f"Place your {self.ships_to_place[0]}-length ship")
        main_layout.addWidget(self.status_label)
        
        # Grid layout for game board
        grid_layout = QGridLayout()
        self.buttons = []
        for row in range(self.board_size):
            row_buttons = []
            for col in range(self.board_size):
                button = QPushButton()
                button.setFixedSize(40, 40)
                button.clicked.connect(lambda _, r=row, c=col: self.place_ship(r, c))
                grid_layout.addWidget(button, row, col)
                row_buttons.append(button)
            self.buttons.append(row_buttons)
        
        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        main_layout.addWidget(grid_widget)
        
        # Card system UI
        self.card_frame = QFrame()
        self.card_layout = QHBoxLayout()
        self.card_frame.setLayout(self.card_layout)
        self.card_frame.setFrameShape(QFrame.StyledPanel)
        self.card_frame.setMinimumHeight(100)
        self.card_frame.hide()  # Hide during ship placement
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.draw_button = QPushButton("Draw Card")
        self.draw_button.clicked.connect(self.draw_card)
        self.draw_button.hide()  # Hide during ship placement
        
        action_layout.addWidget(self.draw_button)
        
        main_layout.addWidget(self.card_frame)
        main_layout.addLayout(action_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def place_ship(self, start_row, start_col):
        if not self.placement_mode:
            return
        
        current_ship_length = self.ships_to_place[0]
        horizontal = self.horizontal_radio.isChecked()
        
        # Check ship placement validity
        try:
            if horizontal:
                if start_col + current_ship_length > self.board_size:
                    raise ValueError("Ship extends beyond board")
                
                ship_coords = [(start_row, start_col + i) for i in range(current_ship_length)]
                
                # Check for overlaps
                if any(self.grid[r][c] == 1 for r, c in ship_coords):
                    raise ValueError("Ship overlaps with existing ship")
                
                # Place ship
                for r, c in ship_coords:
                    self.grid[r][c] = 1
                    self.buttons[r][c].setStyleSheet("background-color: gray;")
                
                self.placed_ships.append(ship_coords)
            else:
                if start_row + current_ship_length > self.board_size:
                    raise ValueError("Ship extends beyond board")
                
                ship_coords = [(start_row + i, start_col) for i in range(current_ship_length)]
                
                # Check for overlaps
                if any(self.grid[r][c] == 1 for r, c in ship_coords):
                    raise ValueError("Ship overlaps with existing ship")
                
                # Place ship
                for r, c in ship_coords:
                    self.grid[r][c] = 1
                    self.buttons[r][c].setStyleSheet("background-color: gray;")
                
                self.placed_ships.append(ship_coords)
            
            # Remove current ship length
            self.ships_to_place.pop(0)
            
            # Update status
            if self.ships_to_place:
                self.status_label.setText(f"Place your {self.ships_to_place[0]}-length ship")
            else:
                self.placement_mode = False
                self.status_label.setText("Ship placement complete!")
                self.parent().check_placement_complete()
        
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Placement", str(e))
    
    def attack_mode(self, enemy_board):
        # Reset buttons for attack phase
        for row in range(self.board_size):
            for col in range(self.board_size):
                self.buttons[row][col].setStyleSheet("")
                self.buttons[row][col].clicked.disconnect()
                self.buttons[row][col].clicked.connect(lambda _, r=row, c=col: self.attack(enemy_board, r, c))
        
        self.enemy_board = enemy_board
        
        # Show card UI
        self.card_frame.show()
        self.draw_button.show()
        
        # Give initial cards
        for _ in range(3):
            self.draw_card(initial=True)
    
    def attack(self, enemy_board, row, col):
        if self.game_over or not self.parent().current_player == self or not self.selected_card:
            return
        
        # Check if attacks are disabled (EMP effect)
        if enemy_board.attacks_disabled and self.selected_card.special_type != "EMP":
            QMessageBox.information(self, "Attacks Disabled", 
                                    f"Your attacks are disabled for this turn due to an EMP!")
            return
        
        # Handle special card types
        if self.selected_card.special_type == "EMP":
            # Apply EMP effect to enemy
            enemy_board.attacks_disabled = True
            QMessageBox.information(self, "EMP Deployed", 
                                    f"You've disabled {enemy_board.player_name}'s attacks for the next turn!")
            
            # Remove card and end turn
            self.remove_card(self.selected_card)
            self.selected_card = None
            self.parent().switch_turns()
            return
            
        elif self.selected_card.special_type == "ReconDrone":
            # Get coordinates to reveal
            coords_to_reveal = self.selected_card.use(enemy_board, row, col)
            
            ship_found = False
            for r, c in coords_to_reveal:
                # Skip invalid coordinates
                if r < 0 or r >= self.board_size or c < 0 or c >= self.board_size:
                    continue
                    
                # Mark cell as revealed
                self.revealed_cells.add((r, c))
                
                # Check if there's a ship part without attacking
                for ship in enemy_board.placed_ships:
                    if (r, c) in ship:
                        ship_found = True
                        self.buttons[r][c].setStyleSheet("background-color: yellow;")  # Highlight without attacking
                        break
                else:
                    # No ship found
                    self.buttons[r][c].setStyleSheet("background-color: lightblue;")  # Different color for revealed empty
            
            if ship_found:
                QMessageBox.information(self, "Recon Complete", "Ships detected in the scanned area!")
            else:
                QMessageBox.information(self, "Recon Complete", "No ships detected in the scanned area.")
                
            # Remove card and end turn
            self.remove_card(self.selected_card)
            self.selected_card = None
            self.parent().switch_turns()
            return
            
        elif self.selected_card.special_type == "SonarPing":
            # Get 5x5 area around target
            ping_area = [(r, c) for r in range(row-2, row+3) for c in range(col-2, col+3) 
                         if 0 <= r < self.board_size and 0 <= c < self.board_size]
            
            # Check if any ships in the area
            ship_found = False
            for r, c in ping_area:
                for ship in enemy_board.placed_ships:
                    if (r, c) in ship:
                        ship_found = True
                        break
                if ship_found:
                    break
            
            # Highlight the entire ping area with a specific color
            for r, c in ping_area:
                self.buttons[r][c].setStyleSheet("background-color: lightcyan;")
            
            if ship_found:
                QMessageBox.information(self, "Sonar Ping", "Ships detected in the area!")
            else:
                QMessageBox.information(self, "Sonar Ping", "No ships detected in the area.")
                
            # Remove card and end turn
            self.remove_card(self.selected_card)
            self.selected_card = None
            self.parent().switch_turns()
            return
            
        elif self.selected_card.name == "Sniper Shot":
            # Special handling for Sniper Shot to bypass previously missed shots
            button = self.buttons[row][col]
            
            # Skip if already hit (red)
            if button.styleSheet() == "background-color: red;":
                QMessageBox.information(self, "Invalid Target", "This position has already been hit!")
                return
            
            # Continue even if it was a previous miss
            coords_to_attack = [(row, col)]
        else:
            # Use selected card to attack
            coords_to_attack = self.selected_card.use(enemy_board, row, col)
        
        # Process all attacks
        hit_found = False
        for r, c in coords_to_attack:
            # Skip invalid coordinates
            if r < 0 or r >= self.board_size or c < 0 or c >= self.board_size:
                continue
                
            button = self.buttons[r][c]
            
            # Skip already hit cells (red) but allow attacking missed cells (white) for normal cards
            if button.styleSheet() == "background-color: red;":
                continue
                
            # Check if hit
            for ship in enemy_board.placed_ships:
                if (r, c) in ship:
                    button.setStyleSheet("background-color: red;")
                    ship.remove((r, c))
                    hit_found = True
                    
                    # Check if ship is sunk
                    if not ship:
                        enemy_board.placed_ships.remove(ship)
                        QMessageBox.information(self, "Ship Sunk!", f"A ship has been sunk in {enemy_board.player_name}'s fleet!")
                    
                    # Check for game over
                    if not enemy_board.placed_ships:
                        self.game_over = True
                        QMessageBox.information(self, "Game Over", f"{self.player_name} wins!")
                        self.parent().end_game()
                    break
            else:
                # Miss
                button.setStyleSheet("background-color: white;")
        
        if hit_found:
            self.status_label.setText("HIT!")
        else:
            self.status_label.setText("Miss...")
        
        # Remove used card from hand
        self.remove_card(self.selected_card)
        self.selected_card = None
        
        # Switch turns
        self.parent().switch_turns()
    
    def draw_card(self, initial=False):
        if len(self.hand) >= self.hand_size:
            QMessageBox.warning(self, "Hand Full", "Your hand is full! Use a card before drawing.")
            return
        
        card = self.parent().get_random_card()
        self.hand.append(card)
        self.update_card_display()
        
        # End turn if not initial draw
        if not initial and self.parent().current_player == self:
            self.parent().switch_turns()
    
    def update_card_display(self):
        # Clear current card display
        for button in self.card_buttons:
            self.card_layout.removeWidget(button)
            button.deleteLater()
        self.card_buttons = []
        
        # Add cards to display
        for card in self.hand:
            card_button = QPushButton(f"{card.name}\n{card.description}")
            card_button.setMinimumWidth(120)
            card_button.setMinimumHeight(80)
            card_button.clicked.connect(partial(self.select_card, card))
            
            # Highlight selected card
            if self.selected_card == card:
                card_button.setStyleSheet("background-color: lightblue; font-weight: bold;")
            
            self.card_layout.addWidget(card_button)
            self.card_buttons.append(card_button)
    
    def select_card(self, card):
        self.selected_card = card
        self.status_label.setText(f"Selected {card.name}. Click on board to attack.")
        self.update_card_display()
    
    def remove_card(self, card):
        if card in self.hand:
            self.hand.remove(card)
            self.update_card_display()

class BattleshipApp(QWidget):
    def __init__(self):
        super().__init__()
        self.players_ready = 0
        self.init_game()
        self.init_cards()
    
    def init_game(self):
        layout = QHBoxLayout()
        
        self.player1_board = BattleshipGame("Player 1")
        self.player2_board = BattleshipGame("Player 2")
        
        layout.addWidget(self.player1_board)
        layout.addWidget(self.player2_board)
        
        self.setLayout(layout)
        
        # Set up turn management
        self.player1_board.setParent(self)
        self.player2_board.setParent(self)
    
    def init_cards(self):
        # Define different card effects
        self.card_pool = [
            Card("Standard", "Basic attack", 
                 lambda board, row, col: [(row, col)]),
            Card("Vertical", "Hits tile above and below", 
                 lambda board, row, col: [(row-1, col), (row, col), (row+1, col)]),
            Card("Horizontal", "Hits tile left and right", 
                 lambda board, row, col: [(row, col-1), (row, col), (row, col+1)]),
            Card("Cross", "Hits four adjacent tiles", 
                 lambda board, row, col: [(row-1, col), (row, col-1), (row, col), (row, col+1), (row+1, col)]),
            Card("45DegCross", "Hits four diagonal tiles", 
                 lambda board, row, col: [(row-1, col-1), (row-1, col+1), (row, col), (row+1, col-1), (row+1, col+1)]),
            Card("RandomHit", "Hits random tile in 3x3 area", 
                 lambda board, row, col: [(row + random.randint(-1, 1), col + random.randint(-1, 1))]),
        ]
        
        # Add RandomEffect card
        def random_effect(board, row, col):
            # Choose a random card except RandomEffect itself
            random_card = random.choice([card for card in self.card_pool if card.name != "RandomEffect"])
            return random_card.use(board, row, col)
        
        self.card_pool.append(Card("RandomEffect", "Uses random effect", random_effect))
        
        # Add new cards
        self.card_pool.extend([
            Card("Bombardment", "Hits a 3x3 area", 
                 lambda board, row, col: [(r, c) for r in range(row-1, row+2) for c in range(col-1, col+2)]),
            Card("Sniper Shot", "Precise attack, ignores misses", 
                 lambda board, row, col: [(row, col)]),  # Special handling in attack method
            Card("Torpedo", "Hits all tiles in a straight line", 
                 lambda board, row, col: [(r, col) for r in range(board.board_size)]),
            Card("Depth Charge", "Hits 2x2 area randomly chosen around target", 
                 lambda board, row, col: [(row + random.choice([-1, 0]), col + random.choice([-1, 0])),
                                          (row + random.choice([-1, 0]), col + random.choice([0, 1])),
                                          (row + random.choice([0, 1]), col + random.choice([-1, 0])),
                                          (row + random.choice([0, 1]), col + random.choice([0, 1]))]),
            Card("EMP", "Disables enemy attacks for a turn", 
                 lambda board, row, col: [], special_type="EMP"),
            Card("Recon Drone", "Reveals a 3x3 area without attacking", 
                 lambda board, row, col: [(r, c) for r in range(row-1, row+2) for c in range(col-1, col+2)], 
                 special_type="ReconDrone"),
            Card("Cluster Bomb", "Hits target and random tiles in radius", 
                 lambda board, row, col: [(row, col)] + [(row + random.randint(-2, 2), col + random.randint(-2, 2)) 
                                                         for _ in range(3)]),
            Card("Sonar Ping", "Reveals if ships in 5x5 area", 
                 lambda board, row, col: [], special_type="SonarPing"),
        ])
    
    def get_random_card(self):
        return random.choice(self.card_pool)
    
    def check_placement_complete(self):
        self.players_ready += 1
        
        # Start game when both players complete placement
        if self.players_ready == 2:
            # Transition to attack phase
            self.player1_board.attack_mode(self.player2_board)
            self.player2_board.attack_mode(self.player1_board)
            
            # Set window titles
            self.player1_board.setWindowTitle(f"Battleship - {self.player1_board.player_name}")
            self.player2_board.setWindowTitle(f"Battleship - {self.player2_board.player_name}")
            
            # Set up turn-based game
            self.current_player = self.player1_board
            self.other_player = self.player2_board
            
            self.current_player.status_label.setText("Your turn - Select a card to attack or draw a card")
            self.other_player.status_label.setText("Waiting...")
    
    def switch_turns(self):
        # Reset EMP effect at turn end
        self.current_player.attacks_disabled = False
        
        # Swap current and other player
        self.current_player, self.other_player = self.other_player, self.current_player
        
        # Update status labels
        if self.current_player.attacks_disabled:
            self.current_player.status_label.setText("Your turn - Your attacks are disabled by EMP! Draw a card.")
        else:
            self.current_player.status_label.setText("Your turn - Select a card to attack or draw a card")
        self.other_player.status_label.setText("Waiting...")
    
    def end_game(self):
        # Disable all buttons
        for board in [self.player1_board, self.player2_board]:
            for row in board.buttons:
                for button in row:
                    button.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    game = BattleshipApp()
    game.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



# ------------------------------------
# --- BATTLESHIP GAME LOGIC Update ---
# ------------------------------------

# Modified sonar ping implementation and hit protection

def attack(self, enemy_board, row, col):
    if self.game_over or not self.parent().current_player == self or not self.selected_card:
        return
    
    # Check if attacks are disabled (EMP effect)
    if enemy_board.attacks_disabled and self.selected_card.special_type != "EMP":
        QMessageBox.information(self, "Attacks Disabled", 
                                f"Your attacks are disabled for this turn due to an EMP!")
        return
    
    # Handle special card types
    if self.selected_card.special_type == "EMP":
        # Apply EMP effect to enemy
        enemy_board.attacks_disabled = True
        QMessageBox.information(self, "EMP Deployed", 
                                f"You've disabled {enemy_board.player_name}'s attacks for the next turn!")
        
        # Remove card and end turn
        self.remove_card(self.selected_card)
        self.selected_card = None
        self.parent().switch_turns()
        return
        
    elif self.selected_card.special_type == "ReconDrone":
        # Get coordinates to reveal
        coords_to_reveal = self.selected_card.use(enemy_board, row, col)
        
        ship_found = False
        for r, c in coords_to_reveal:
            # Skip invalid coordinates
            if r < 0 or r >= self.board_size or c < 0 or c >= self.board_size:
                continue
                
            # Skip already hit cells (red)
            if self.buttons[r][c].styleSheet() == "background-color: red;":
                continue
                
            # Mark cell as revealed
            self.revealed_cells.add((r, c))
            
            # Check if there's a ship part without attacking
            for ship in enemy_board.placed_ships:
                if (r, c) in ship:
                    ship_found = True
                    self.buttons[r][c].setStyleSheet("background-color: yellow;")  # Highlight without attacking
                    break
            else:
                # No ship found
                self.buttons[r][c].setStyleSheet("background-color: lightblue;")  # Different color for revealed empty
        
        if ship_found:
            QMessageBox.information(self, "Recon Complete", "Ships detected in the scanned area!")
        else:
            QMessageBox.information(self, "Recon Complete", "No ships detected in the scanned area.")
            
        # Remove card and end turn
        self.remove_card(self.selected_card)
        self.selected_card = None
        self.parent().switch_turns()
        return
        
    elif self.selected_card.special_type == "SonarPing":
        # Get 5x5 area around target
        ping_area = [(r, c) for r in range(row-2, row+3) for c in range(col-2, col+3) 
                     if 0 <= r < self.board_size and 0 <= c < self.board_size]
        
        # Count ships in the area without revealing exact locations
        ship_count = 0
        ship_cells = set()
        
        for r, c in ping_area:
            # Check each ship
            for ship in enemy_board.placed_ships:
                if (r, c) in ship:
                    ship_cells.add((r, c))
                    break
        
        ship_count = len(ship_cells)
        
        # Highlight the entire ping area with a specific color, except for already hit cells
        for r, c in ping_area:
            # Never change color of hit cells (red)
            if self.buttons[r][c].styleSheet() != "background-color: red;":
                self.buttons[r][c].setStyleSheet("background-color: lightcyan;")
        
        if ship_count > 0:
            QMessageBox.information(self, "Sonar Ping", f"Detected {ship_count} ship cells in the area!")
        else:
            QMessageBox.information(self, "Sonar Ping", "No ships detected in the area.")
            
        # Remove card and end turn
        self.remove_card(self.selected_card)
        self.selected_card = None
        self.parent().switch_turns()
        return
        
    elif self.selected_card.name == "Sniper Shot":
        # Special handling for Sniper Shot to bypass previously missed shots
        button = self.buttons[row][col]
        
        # Skip if already hit (red)
        if button.styleSheet() == "background-color: red;":
            QMessageBox.information(self, "Invalid Target", "This position has already been hit!")
            return
        
        # Continue even if it was a previous miss
        coords_to_attack = [(row, col)]
    else:
        # Use selected card to attack
        coords_to_attack = self.selected_card.use(enemy_board, row, col)
    
    # Process all attacks
    hit_found = False
    for r, c in coords_to_attack:
        # Skip invalid coordinates
        if r < 0 or r >= self.board_size or c < 0 or c >= self.board_size:
            continue
            
        button = self.buttons[r][c]
        
        # Skip already hit cells (red) but allow attacking missed cells (white) for normal cards
        if button.styleSheet() == "background-color: red;":
            continue
            
        # Check if hit
        for ship in enemy_board.placed_ships:
            if (r, c) in ship:
                button.setStyleSheet("background-color: red;")
                ship.remove((r, c))
                hit_found = True
                
                # Check if ship is sunk
                if not ship:
                    enemy_board.placed_ships.remove(ship)
                    QMessageBox.information(self, "Ship Sunk!", f"A ship has been sunk in {enemy_board.player_name}'s fleet!")
                
                # Check for game over
                if not enemy_board.placed_ships:
                    self.game_over = True
                    QMessageBox.information(self, "Game Over", f"{self.player_name} wins!")
                    self.parent().end_game()
                break
        else:
            # Miss
            button.setStyleSheet("background-color: white;")
    
    if hit_found:
        self.status_label.setText("HIT!")
    else:
        self.status_label.setText("Miss...")
    
    # Remove used card from hand
    self.remove_card(self.selected_card)
    self.selected_card = None
    
    # Switch turns
    self.parent().switch_turns()

# Also update the card definition in init_cards method
def init_cards(self):
    # [Keep all other card definitions the same]
    
    # Update the Sonar Ping card description
    self.card_pool.extend([
        # [Keep other cards the same]
        Card("Sonar Ping", "Reports number of ship cells in 5x5 area", 
             lambda board, row, col: [], special_type="SonarPing"),
        # [Keep other cards the same]
    ])