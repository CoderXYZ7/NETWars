
# NETWars
## Design philosophy
NETWars is a strategy game inspired by battleship, a game based on luck and pattern prevision.
### Design Rules
1. The player should be always able to win, independently from the state of play.
2. Randomness is emphasized.
3. The artistic direction is Pixel-art.
## Involved Technologies
- Docker
- Html
- Maria DB
- SQL
- JavaScript
- CSS
- PHP
- Python

## How it will work on the technical side of things

| Name | Docker | Scope | Techs |
| ------------ | ------------ | ------------ | ------------ |
| Backend | nw-backend | managing the game logic | Python(?) SQL |
| Frontend | nw-frontend | displaying the interface to the user | Html CSS PHP JS |
| Database | nw-db | storing the data of the players an game | Maria DB SQL |

### Docker
The game will be running on a system called Docker.
Docker is a platform that enables developers to automate the deployment of applications within lightweight, portable containers. These containers package the application code along with its dependencies, ensuring consistent behavior across various environments, from development to production.
This will enable us to build the one of the parts of the game at a time without the need of having the other two already in development.

As said before we will have 3 containers:

### Backend
It will be an API container that will manage the communications between the Frontend and the DB.
It will be written in Python (probably) using a network library like Flask, that makes possible to interrogate the DB trough a secure connection between the Frontend and the Backend, without exposing the DB credentials.

### Frontend
It will be a simple Html page with all the required languages to make it pretty an working.
This will be the interface between the user and the game.

### Batabase
The DB will store all the data in tables for the game and the users.

## Gameplay
The gameplay will be turn based, at the start of the game the player will have a cache of fishes from random pool, the fishes are used as ammo to sink the enemy boats.
The fish-trowing system works on a First in-First out.
The fishes will be a limited resource that must be replenished by fishing a card (this wordplay works better in Italian).
There are fishes that have special abilities of disabilities.
Those include but are not limited to:
- Exploding Fish
- Poison Fish
- Dumb Fish
- Flying Fish
- Instant use
- Heat seaking fish
- Hit in strange patterns Fish
- Long Fish
- Average Fish
- F.I.S.H.

In his turn the player will have to chose between trowing a fish and fishing a fish.

# Interface
The interface will be divided in tree pages, a login page, a game selection page and a game page.
The login page is a simple page where one can register (simply inserting a username and password that will be added to the database trough the backend) or login with his credentials.
The game selection page is a page where the player can create a new match, defining simply a name for the match (and optionally a password), than the page will show all the games in a column, with 3 buttons, enter as player 1, enter as player 2 and spectate. When a player enters as player 1 or 2 the button will be grayed-out, to enter will be necessary the password, if the game has one.
Than we have the game interface, with simply a zone where the player has his ships, a zone where the enemy has his ships and a list of fishes, that the player can use as ammo in a system first-it first-out, and a button to pass, when a player passes, a random fish gets added to the query of the fishes.
The game is divided in 2 parts, preparation and warfare, the preparation part is simply a time where the two players place their ships on their zone, and that, when both have pressed pass, the warfare starts, one player gets chosen at random to start and he launches a fish at the enemy or passes, that is the turn of the other player.
The game ends when one player has no more ships.
<!--stackedit_data:
eyJoaXN0b3J5IjpbMzY0MTM4NjUzXX0=
-->