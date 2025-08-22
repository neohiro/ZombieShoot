# ZombieShoot
Zombie Shooter for Linux/Windows

ZombieShoot.PY
- A fast-paced, top-down zombie shooter game built with Pygame. Survive endless waves of the undead, upgrade your weapons, and climb the leaderboards in this retro-inspired arcade action title.

Features

- Dynamic Gameplay: Face off against an ever-increasing horde of zombies with a simple and intuitive top-down perspective.
- Weapon Upgrades: Start with a basic pistol and progress to powerful weapons like the machine gun and the devastating Gatling gun.
- Procedural Generation: The game world features a procedurally generated hexagonal floor pattern, ensuring every session feels unique.
- Persistent Leaderboards: Your high scores are saved, allowing you to track your progress and compete against yourself to survive longer.
- Customizable Controls: The game's controls can be fully remapped in the options menu to suit your play style.
- In-House Sound Generation: All sound effects and the main menu music are generated programmatically, providing a unique and consistent audio experience.
- Visual Effects: Get into the action with visual feedback from blood splatters and particle effects when you take down a zombie.

How to Play
- Run the Game: Make sure you have Pygame installed (pip install pygame) and then run the Python script.

Controls:

- Movement: Use the W, A, S, D keys or the arrow keys to move your character.
- Shooting: Aim with your mouse and click to shoot.
- Survive: Your goal is to survive for as long as possible while your score increases. As time goes on, the zombie waves will become more difficult.
- Power-Ups: Keep an eye out for health-restoring power-ups to stay in the fight longer.

Technical Details
- Language: Python
- Libraries: pygame, numpy, math, random
- Game Loop: The core of the game is a robust state machine that handles transitions between the main menu, options, leaderboards, and the primary game loop.
- Object-Oriented Design: The game is structured with classes for Player, Zombie, Bullet, PowerUp, and other game entities, making the code clean and easy to manage.

Installation
To get started, simply download this repository and install the required libraries:

    git clone https://github.com/neohiro/ZombieShoot.git
    cd zombie-shoot
    pip install pygame
    python ZombieShoot.PY

Contributing
- Feel free to open an issue or submit a pull request if you have ideas for new features or improvements!

Developed by: http://frenzypenguin.media
