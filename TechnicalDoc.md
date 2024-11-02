---

# NETWars Technical Document

## Overview
NETWars is a turn-based strategy game, played within a browser interface, using containerized architecture to separate backend, frontend, and database functionalities. The project emphasizes simplicity in design with pixel-art aesthetics, controlled randomness, and player interactivity.

---

## Technical Requirements

### Technology Stack
- **Frontend**: HTML, CSS, JavaScript, PHP
- **Backend**: Python (using Flask for API services)
- **Database**: MariaDB with SQL
- **Containerization**: Docker

### Containers and Services

1. **Backend** (`nw-backend`)
   - **Purpose**: Manages game logic, handles API requests, processes player moves, and coordinates with the database.
   - **Technology**: Python (Flask recommended)
   - **Responsibilities**:
     - Provide a RESTful API for frontend interactions.
     - Handle game state transitions (e.g., start game, process moves, end game).
     - Manage turn-based logic and random fish selection.
     - Securely communicate with the database, hiding DB credentials from the frontend.
   - **Endpoints**:
     - **POST /register**: Registers a new user (accepts username and password).
     - **POST /login**: Authenticates user login.
     - **POST /new_game**: Creates a new game session (with optional password).
     - **POST /join_game**: Allows a player to join an existing game.
     - **GET /game_state**: Returns current game status and player information.
     - **POST /action**: Processes game actions (throw fish, pass turn, etc.).
     - **POST /end_turn**: Handles the player’s choice to pass, adding a random fish to their inventory.
   - **Error Handling**: Return appropriate HTTP status codes and messages for common errors, like invalid login or unauthorized game access.

2. **Frontend** (`nw-frontend`)
   - **Purpose**: Provides the user interface for gameplay, user registration, and game management.
   - **Technology**: HTML, CSS, JavaScript, PHP
   - **Responsibilities**:
     - **Login Page**: Allows users to register or log in to access the game selection page.
     - **Game Selection Page**: Lists active games with options to create, join as Player 1 or Player 2, or spectate.
       - UI displays active games and handles password input for restricted games.
       - Manages greyed-out buttons to restrict game roles when filled.
     - **Game Interface**: Displays two zones (player and opponent), inventory of fishes, and action buttons (throw, pass).
       - Visual cues for fish properties (e.g., Exploding Fish, Poison Fish).
       - FIFO system for fish deployment.
       - Real-time turn status updates (initiated by backend responses).
   - **Additional Features**:
     - Dynamic CSS to enhance the pixel-art style.
     - JavaScript for asynchronous updates and smooth gameplay transitions.

3. **Database** (`nw-db`)
   - **Purpose**: Stores all persistent data, including user accounts, game sessions, and player moves.
   - **Technology**: MariaDB, SQL
   - **Responsibilities**:
     - **Tables**:
       - **Users**: Stores `user_id`, `username`, `password_hash`.
       - **Games**: Stores `game_id`, `name`, `status`, `player_1`, `player_2`, `password`.
       - **GameState**: Stores `game_id`, `player_id`, `fish_inventory`, `ship_positions`, `turn`.
     - Secure storage of user credentials with hashing.
     - Efficient querying for game sessions and real-time state updates.

---

## Gameplay Flow and Logic

### Game States

1. **Login/Registration**:
   - Users create an account or log in.
   - Backend validates credentials and generates a session.

2. **Game Selection**:
   - Users create or join a game session.
   - If creating, backend assigns a unique game ID and initializes game state.
   - If joining, backend validates password if required and assigns the user as Player 1 or Player 2.

3. **In-Game (Preparation Phase)**:
   - Players place their ships within their designated area.
   - Once both players confirm their placements, the backend transitions the game to the Warfare phase.

4. **In-Game (Warfare Phase)**:
   - Turns are managed by the backend, which randomly selects the first player.
   - Players choose to throw a fish or pass.
     - Backend processes fish type, targeting, and effects (e.g., Exploding Fish damages a specific area).
     - If the player passes, backend adds a random fish to their inventory.
   - Game ends when one player’s ships are entirely destroyed.

---

## API and Data Handling

### Data Security
- The backend manages all DB connections, ensuring credentials are not exposed to the frontend.
- Sensitive data (e.g., passwords) is hashed and securely stored.

### Data Flow
1. **Frontend to Backend**: Requests are sent for actions like login, game creation, and in-game moves.
2. **Backend to Database**: Backend queries data as needed, ensuring secure and efficient data handling.
3. **Backend to Frontend**: Backend responses provide real-time game updates, including game status, turn results, and inventory changes.

---

## Docker Configuration

Each component is isolated within its container:
- **nw-backend**: Hosts the Flask API to handle game logic and connect to the database.
- **nw-frontend**: Runs a PHP server serving HTML, CSS, and JavaScript for the user interface.
- **nw-db**: MariaDB container managing all game and user data storage.

---

## Technical Tasks Breakdown

1. **Backend Development**:
   - Implement Flask endpoints for user authentication, game management, and in-game actions.
   - Integrate SQL queries to manage player and game state.
2. **Frontend Development**:
   - Design and implement the login, game selection, and game interfaces.
   - Implement AJAX calls to update game status in real-time.
3. **Database Schema**:
   - Set up tables for users, games, and game state.
   - Test data retrieval and manipulation queries.
4. **Dockerization**:
   - Set up Docker containers for each service and test inter-service communication.

--- 
<!--stackedit_data:
eyJoaXN0b3J5IjpbMTY2OTA1MDM2XX0=
-->