---

# NETWars Technical Document

## Overview
NETWars is a turn-based, browser-based strategy game inspired by classic Battleship mechanics but enhanced with unique fish-based attacks and pixel-art styling. The game emphasizes randomness and encourages strategic pattern recognition, keeping the player engaged and able to win regardless of the current game state.

---

## Technical Requirements

### Technology Stack
- **Frontend**: HTML, CSS, JavaScript, PHP
- **Backend**: Python (using Flask for API services)
- **Database**: MariaDB with SQL
- **Containerization**: Docker

---

## Gameplay

### Core Mechanics
1. **Turn-Based Play**:
   - Players take turns throwing fish at their opponent’s ships or passing to draw a new fish.
   - Each fish serves as “ammo” with a unique effect, requiring strategic choice based on available fish and game state.

2. **Game Phases**:
   - **Preparation Phase**: Players place ships on their grid. Both players must confirm their placements to proceed.
   - **Warfare Phase**: Players take turns choosing actions (throw fish or pass) to attack or draw new fish.

3. **Fish Types**:
   - Fish have special abilities or traits, influencing gameplay:
     - **Exploding Fish**: Damages multiple tiles around the target.
     - **Poison Fish**: Leaves a poison effect on hit tiles.
     - **Dumb Fish**: Has a chance to miss the intended target.
     - **Flying Fish**: Bypasses certain defenses.
     - **Heat-Seeking Fish**: Targets ships if they are near the selected tile.
     - **Long Fish**: Travels across multiple tiles.
   - **Inventory System**: Players manage fish in a FIFO (First-In-First-Out) inventory, adding a layer of resource management to gameplay.

4. **Game Over Conditions**:
   - The game ends when a player’s last ship is destroyed.

5. **Game Interface**:
   - **Grid Layout**: Shows the player’s ships and a hidden grid for the opponent’s ships.
   - **Action Buttons**: Players choose to throw a fish or pass (to draw a new fish).
   - **Inventory Display**: Shows available fish and their effects, organized in a FIFO order.

---

## Functional Components

### 1. Dockerized Services

#### Overview
Each component runs as an isolated Docker container to maintain modularity and streamline deployment.

#### Components

| Component  | Docker Service | Description                        | Technologies    |
|------------|----------------|------------------------------------|-----------------|
| **Backend**| `nw-backend`   | Manages game logic and API calls   | Python, SQL     |
| **Frontend**| `nw-frontend` | Presents UI to players             | HTML, CSS, JS, PHP |
| **Database**| `nw-db`       | Stores player and game data        | MariaDB, SQL    |


---

### 2. Backend (`nw-backend`)

- **Purpose**: Manages game logic, handles API requests, processes player actions, and coordinates with the database.
- **Technology**: Python (using Flask for the API)
- **Responsibilities**:
  - **User Authentication**: Handle registration, login, and user sessions.
  - **Game Session Management**: Initialize game sessions, store game state, and manage player roles (Player 1, Player 2, Spectator).
  - **Gameplay Actions**:
    - Handle player moves (throw fish, pass turn).
    - Manage fish effects on the game grid.
    - Randomize turn assignment and fish replenishment.
  - **Endpoints**:
    - **POST /register**: Registers a new user with a hashed password.
    - **POST /login**: Authenticates users.
    - **POST /new_game**: Creates a new game session.
    - **POST /join_game**: Allows players to join a game.
    - **GET /game_state**: Retrieves current game state.
    - **POST /action**: Handles in-game actions (throw fish, pass).
- **Error Handling**: Provides clear error messages and HTTP status codes for actions like invalid login or game access violations.

### 3. Frontend (`nw-frontend`)

- **Purpose**: Serves as the player interface for gameplay, user registration, and game management.
- **Technology**: HTML, CSS, JavaScript, PHP
- **Pages**:
  - **Login Page**: Allows user registration and login.
  - **Game Selection Page**: Lists active games and allows users to join or create games.
    - Displays game details and access options (Player 1, Player 2, Spectator).
    - Handles password input for restricted games.
  - **Game Interface**: Displays:
    - **Player’s Zone**: Player’s ships and fish inventory.
    - **Opponent’s Zone**: Hidden grid representing the opponent’s side.
    - **Action Panel**: Buttons to throw a fish or pass.
    - **Inventory List**: Shows FIFO-ordered fish inventory and fish properties.
- **Visual Style**:
  - Pixel-art styling for a retro aesthetic.
  - Responsive and dynamic updates using JavaScript for smooth game transitions.

### 4. Database (`nw-db`)

- **Purpose**: Stores persistent data, including user accounts, game sessions, and player moves.
- **Technology**: MariaDB, SQL
- **Schema**:
  - **Users Table**: Stores user data with `user_id`, `username`, `password_hash`.
  - **Games Table**: Contains game information with fields like `game_id`, `name`, `status`, `player_1`, `player_2`, and `password` if applicable.
  - **GameState Table**: Holds game-specific data, such as `game_id`, `player_id`, `fish_inventory`, `ship_positions`, and `turn`.
- **Data Security**: Hash all passwords and enforce secure access patterns between frontend and backend.

---

## API and Data Handling

### Data Security and Flow
- **Backend-Controlled DB Access**: DB credentials remain in the backend, securing them from frontend exposure.
- **Data Flow**:
  - **Frontend-to-Backend**: All actions and updates are managed via API requests (e.g., login, game creation, in-game actions).
  - **Backend-to-Database**: Backend securely manages data requests and updates to the database.
  - **Backend-to-Frontend**: Backend responds with JSON data for real-time game updates.

---

## Technical Tasks Breakdown

1. **Backend Development**:
   - Implement Flask API endpoints for user authentication, game creation, and gameplay actions.
   - Integrate SQL queries to manage player data and game state effectively.
   - Handle game logic, turn-based actions, and fish inventory updates.

2. **Frontend Development**:
   - Create the login, game selection, and game interfaces.
   - Use AJAX and JavaScript to manage real-time updates and smooth gameplay transitions.
   - Implement pixel-art-inspired CSS for consistent visual styling.

3. **Database Setup**:
   - Design and set up the database schema with tables for users, games, and game states.
   - Develop SQL queries for efficient data retrieval and storage.

4. **Dockerization**:
   - Set up Docker containers for the backend, frontend, and database.
   - Configure inter-service communication and test for seamless deployment.

---
<!--stackedit_data:
eyJoaXN0b3J5IjpbLTE4MjQ5MjUwMTIsMTY2OTA1MDM2XX0=
-->