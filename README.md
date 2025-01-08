# Invade Spacers

**Invade Spacers** is a simple 2D game that gets you to explore Space! But watch out, the Space race tends to get fast and dangerous, with all the obstacles there is up there...

---
## Main features
- **Dodge the obstacles**: Move your spaceship left or right to avoid obstacles that try to get on your way
- **Infinite game**: A seamless infinitely scrolling map that challenges you to beat your own record 

---
## Structure
This is a school project that aims to work using the ECS design pattern.  <br>
There are three main elements composing this code :
- Entities: the different "things" in the world of the game, represented by an id, for example the **user's spaceship**, **obstacles** 
- Components: they are assigned to each entity to hold the data associated to it, like **Position**, **Velocity**
- Systems: they are in charge of updating the data, like **MovementSystem** or **RenderingSystem**

---
## Requirements
- Python 3.10 or higher
- Pygame 2.0 or higher

---

## Setup

Clone the project

```bash
  git clone https://github.com/aleperdriel/ecs-game.git
```

Go to the project directory

```bash
  cd ecs-game
```

If you don't have them : install dependencies

```bash
  pip install pygame
```

Start the game

```bash
  python main.py