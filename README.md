# Polygon Blasters

Polygon Blasters is a bullet hell (shmup) developed in Python using Pygame.

The game features fast-paced gameplay focused on dodging dense bullet patterns, grazing enemy attacks for bonus score, collecting point items, and defeating increasingly difficult enemies with unique attack behaviors.

Unlike many beginner projects, Polygon Blasters was designed around reusable object-oriented systems that make it easy to add new enemies, bullet patterns, and gameplay mechanics.

---

## Features

- Four unique enemy archetypes
- Multiple bullet pattern algorithms
- Player focus mode
- Precise hitbox system
- Graze mechanic
- Score system
- Extra lives earned through gameplay
- Homing point particles
- Enemy death animations
- Sound effects
- Replay functionality
- Fully object-oriented architecture

---

## Controls

Arrow Keys — Move

Shift — Focus movement (reduced speed)

Z — Shoot

ctrl+r — Replay

---


## Project Structure

project.py
Main game loop and gameplay logic.

img/
Game sprites and artwork.

sfx/
Sound effects used during gameplay.


README.md
Project documentation.

---

## Design Decisions

One of my primary goals was making the game highly expandable.

Rather than creating separate code for every enemy, I implemented an enemy archetype system. Each archetype defines its own artwork, health, hitboxes, and shooting behavior. Enemy movement is handled independently from attack patterns, allowing new combinations without rewriting existing code.

Bullet patterns were implemented as standalone functions instead of embedding them inside enemy classes. This makes it easy to reuse attack patterns across different enemies.

Collision detection is based on circular hitboxes instead of rectangular sprite collisions, making gameplay more accurate and better suited to the bullet hell genre.

The player's graze mechanic rewards risky movement by granting score whenever bullets or enemies pass near—but do not touch—the player.

The project also includes a replay system that completely resets the game state without restarting the application.

---

## Future Plans

Possible future additions may include:

- Boss phases
- New enemy archetypes
- More bullet patterns
- Menus and settings
- Improved visual effects

---

## Open Source

This project is open source.

Feel free to:

- modify gameplay
- redesign graphics
- rebalance enemies
- create new stages
- improve the code

If you make something interesting, I'd love to see it.

---

## Acknowledgements
Created using Python and Pygame.
