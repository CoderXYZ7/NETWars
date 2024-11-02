
Here’s a refined and better-structured version of the README for *NETWars*:

---

# NETWars

## Overview
**NETWars** is a pixel-art strategy game inspired by the classic game Battleship, blending luck and predictive patterns. Players engage in turn-based gameplay, using unique "fish" as weapons to sink enemy ships in a lively and tactical arena.

## Design Philosophy
- **Always Winnable**: The player should always have a path to victory, no matter the game's state.
- **Emphasis on Randomness**: Random elements are central, creating dynamic and unpredictable experiences.
- **Pixel-Art Style**: The visual design embraces a retro pixel-art aesthetic.

## Technologies Used
- **Containerization**: Docker
- **Frontend**: HTML, CSS, JavaScript, PHP
- **Backend**: Python, SQL
- **Database**: MariaDB

---

## Architecture Overview
**NETWars** is composed of three main Docker containers, each with a distinct role:

| Component  | Docker Container | Purpose                       | Technologies              |
|------------|------------------|-------------------------------|---------------------------|
| Backend    | nw-backend       | Game logic management         | Python, SQL               |
| Frontend   | nw-frontend      | User interface                | HTML, CSS, PHP, JavaScript|
| Database   | nw-db            | Player and game data storage  | MariaDB, SQL              |

### Docker
Docker streamlines deployment by packaging the application into isolated containers, ensuring consistent performance across environments. This modular setup allows independent development and testing of each component.

### Backend
The backend container is likely built in Python, utilizing a framework like Flask for API management. It handles secure data exchanges between the frontend and the database, protecting credentials while enabling seamless gameplay.

### Frontend
A simple yet interactive HTML-based interface serves as the user’s portal into *NETWars*. Combining HTML, CSS, JavaScript, and PHP, the frontend makes the game visually appealing and functional.

### Database
Player and game data are stored in a MariaDB database. The database structure organizes game sessions, user credentials, and gameplay data, supporting quick retrieval and updates.

---

## Gameplay
*NETWars* is a turn-based game with a unique twist on resource management. Players use "fish" as ammunition to sink enemy ships, selecting their moves from a pool of randomly drawn fish. Each fish has unique attributes that add strategy and fun to each turn.

- **Ammo Pool**: Players draw fish cards from a random pool, replenishing as they play. 
- **Fish Types**: Some fish have special abilities or drawbacks, adding complexity to gameplay. Examples include:
  - Exploding Fish
  - Poison Fish
  - Heat-Seeking Fish
  - Long Fish
  - Dumb Fish
  - Flying Fish
  - ... and more!

- **Turn Actions**: Players can either throw a fish or draw a new one. The fish queue operates on a First In-First Out basis, introducing strategy in resource management.
  
### Phases of Gameplay
1. **Preparation Phase**: Players place their ships in designated zones. When both are ready, they pass to signal the transition.
2. **Warfare Phase**: A player is randomly chosen to start. Players alternate turns, choosing to launch a fish at enemy ships or pass. When passing, a random fish is added to their queue.
3. **Victory**: The game ends when one player loses all their ships.

---

## User Interface
The interface is divided into three main pages:

1. **Login Page**: 
   - Players register or log in, entering usernames and passwords, which are securely saved in the database.

2. **Game Selection Page**:
   - Players can create new matches (with optional passwords).
   - Each game displays three options: join as Player 1, join as Player 2, or spectate.
   - When one player joins as Player 1 or 2, the option is disabled for others.
  
3. **Game Page**:
   - Displays the player’s and enemy’s ships.
   - Shows the player’s queue of fish, which can be used as ammo.
   - Contains a pass button that, when pressed, adds a random fish to the queue.

---

**NETWars** combines classic strategy with fresh, unpredictable gameplay elements, making each match a unique challenge. We look forward to bringing this game to life with our dedicated use of modern web and game development technologies.
<!--stackedit_data:
eyJoaXN0b3J5IjpbNTAyMjQ3OTMsMzY0MTM4NjUzXX0=
-->