import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt

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
        
        main_layout.addLayout(grid_layout)
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
    
    def attack(self, enemy_board, row, col):
        if self.game_over or not self.parent().current_player == self:
            return
        
        button = self.buttons[row][col]
        
        # Check if hit
        for ship in enemy_board.placed_ships:
            if (row, col) in ship:
                button.setStyleSheet("background-color: red;")
                ship.remove((row, col))
                
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
        
        # Disable button after attack
        button.setEnabled(False)
        
        # Switch turns
        self.parent().switch_turns()

class BattleshipApp(QWidget):
    def __init__(self):
        super().__init__()
        self.players_ready = 0
        self.init_game()
    
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
            
            self.current_player.status_label.setText("Your turn to attack!")
            self.other_player.status_label.setText("Waiting...")
    
    def switch_turns(self):
        # Swap current and other player
        self.current_player, self.other_player = self.other_player, self.current_player
        
        # Update status labels
        self.current_player.status_label.setText("Your turn to attack!")
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