from __future__ import annotations
import pygame
import random
from functools import reduce
from typing import Tuple

# Constant game variables
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 800
FPS = 60

TITLE = "INVADE SPACERS"
HOME_TEXT = "Welcome to" + TITLE + "! Let's conqueer Space"
SPEED = 7

# Assets loading
BG_PATH = "assets/backgrounds/Space_Stars6.png"
SHIP_PATH = "assets/ships/purple.png"
ENEMY_PATH = "assets/ships/brown.png"

Entity = int
Bitmask = int


class Component:
    pass

class System:
    def __call__(self, world: World, dt: float) -> None:
        pass


class World:
    EMPTY_BITMASK: Bitmask = 0b00000000

    def __init__(self) -> None:
        self.entities = list(range(100))

        # Remaining available entities
        self.entities_pool = list(self.entities)

        # Create bitmasks for each entity
        self.entities_comps = [self.EMPTY_BITMASK] * len(self.entities)
        self.entities_comps_data = [{} for _ in self.entities]

        self.comps = list(range(16))
        self.comps_pool = list(self.comps)
        self.comps_map: dict[type[Component], int] = {}

    
    def add_entity(self) -> Entity:
        if not len(self.entities_pool):
            raise IndexError(f"The maximum of {len(self.entities)} entities has been reached")

        ent = self.entities_pool.pop()
        self.entities_comps[ent] = self.EMPTY_BITMASK
        return ent

    def remove_entity(self, ent: Entity) -> None:
        self.entities_comps[ent] = self.EMPTY_BITMASK
        self.entities_comps_data[ent] = {}
        self.entities_pool.append(ent)

    def assign_component(self, ent: Entity, comp: type[Component], data: Component) -> None:
        self.entities_comps[ent] |= self.component_bitmask(comp)
        self.entities_comps_data[ent][comp] = data

    def unassign_component(self, ent: Entity, comp: type[Component]) -> None:
        self.entities_comps[ent] &= ~self.component_bitmask(comp)
        if comp in self.entities_comps_data[ent]:
            del self.entities_comps_data[ent][comp]

    def register_component(self, comp: type[Component]) -> Bitmask:
        if not len(self.comps_pool):
            raise IndexError(f"The maximum count of {len(self.comps)} components has been reached")
        if comp not in self.comps_map:
            self.comps_map[comp] = self.comps_pool.pop()
        return self.component_bitmask(comp)

    def component_bitmask(self, comp: type[Component]) -> Bitmask:
        return 1 << self.comps_map[comp]

    def query_bitmask(self, *query: type[Component]) -> Bitmask:
        return reduce(lambda a, b: a | b, (self.component_bitmask(comp) for comp in query))

    def query(self, *query: type[Component]) -> list[Entity]:
        bitmask = self.query_bitmask(*query)
        return [i for i, b in enumerate(self.entities_comps) if b & bitmask == bitmask]


# Components
class Position(Component):
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, dx: float, dy: float) -> None:
        self.dx = dx
        self.dy = dy


class Sprite(Component):
    def __init__(self, path: str, size: Tuple[int, int] = None) -> None:
        self.og_image = pygame.image.load(path)
        self.og_size = (self.og_image.get_width(), self.og_image.get_height())
        if size != self.og_size and size != None : 
            self.image = pygame.transform.scale(self.og_image, size)
            self.size = size
        else : 
            self.size = self.og_size
            self.image = self.og_image


class Health(Component):
    def __init__(self, hp: int) -> None:
        self.hp = hp

class Background(Component):
    pass

# Systems
class MovementSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        for entity in world.query(Position, Velocity):
            pos = world.entities_comps_data[entity][Position]
            vel = world.entities_comps_data[entity][Velocity]
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt


class ScrollingSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        for entity in world.query(Position, Sprite):
            pos = world.entities_comps_data[entity][Position]
            if pos.y > WINDOW_HEIGHT:
                pos.y = -50



class CollisionSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        ship = world.query(Position, Health)[0]

        ship_pos = world.entities_comps_data[ship][Position]
        ship_sprite = world.entities_comps_data[ship][Sprite]
        ship_health = world.entities_comps_data[ship][Health]

        for obstacle in world.query(Position, Sprite):
            obs_pos = world.entities_comps_data[obstacle][Position]
            obs_render = world.entities_comps_data[obstacle][Sprite]

            # Check collision
            if (
                ship_pos.x < obs_pos.x + obs_render.size[0]
                and ship_pos.x + ship_sprite.size[0] > obs_pos.x
                and ship_pos.y < obs_pos.y + obs_render.size[1]
                and ship_pos.y + ship_sprite.size[1] > obs_pos.y
            ):
                # ship_health.hp -= 1
                world.remove_entity(obstacle)


class RenderingSystem(System):
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def __call__(self, world: World, dt: float) -> None:
        self.screen.fill((0, 0, 0)) 

        # Background needs to be rendered first with Pygame
        self.render_background(world)

        rendered_entities = world.query(Position, Sprite)
        
        for entity in rendered_entities:
            pos = world.entities_comps_data[entity][Position]
            sprite = world.entities_comps_data[entity][Sprite]

            if not Background in world.entities_comps_data[entity]:
                self.screen.blit(sprite.image, (pos.x, pos.y))

        # Display health
        if len((world.query(Position, Health))) > 0:
            ship_health = world.entities_comps_data[world.query(Position, Health)[0]][Health]
            sh = ship_health.hp

        else : sh = 10
        font = pygame.font.Font(None, 36)
        health_text = font.render(f"Health: {sh}", True, (255, 255, 255))
        self.screen.blit(health_text, (10, 10))


        pygame.display.flip()

    def render_background(self, world: World) -> None:
        for entity in world.query(Position, Sprite, Background):  # Only background entities
            pos = world.entities_comps_data[entity][Position]
            sprite = world.entities_comps_data[entity][Sprite]
            
            tile_size = sprite.size[0]
            
            # Render the background with scrolling
            for i in range(0, WINDOW_HEIGHT, tile_size):
                for j in range(-tile_size, WINDOW_WIDTH + tile_size *2, tile_size):
                    self.screen.blit(sprite.image, (i, j + pos.y))


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    

    world = World()

    # Register components
    world.register_component(Position)
    world.register_component(Velocity)
    world.register_component(Sprite)
    world.register_component(Health)
    world.register_component(Background)

    # Create a ship entity
    ship = world.add_entity()    
    ship_pos = Position(WINDOW_WIDTH/2 - 32, WINDOW_HEIGHT - 120)
    world.assign_component(ship, Position, ship_pos)
    world.assign_component(ship, Sprite, Sprite(SHIP_PATH, (86, 86)))
    world.assign_component(ship, Health, Health(5))

    # Create a background
    bg = world.add_entity()
    world.assign_component(bg, Position, Position(0,0))
    world.assign_component(bg, Sprite, Sprite(BG_PATH, (128, 128)))
    world.assign_component(bg, Background, Background)


    # Systems -----------------------------------------------------------------------
    movement_system = MovementSystem()
    scrolling_system = ScrollingSystem()
    # collision_system = CollisionSystem()
    rendering_system = RenderingSystem(screen)

    # Game loop ---------------------------------------------------------------------
    running = True
    
    while running:
        
        # Delta time in seconds
        dt = clock.tick(60) / 1000.0  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Move depending on the key pressed should it be updated with system ?
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            ship_pos.x -= 200 * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ship_pos.x += 200 * dt 

        # Prevent ship from leaving the screen
        ship_pos.x = max(0, min(ship_pos.x, WINDOW_WIDTH - 64))

        # Spawn obstacles randomly
        if random.random() < 0.02:  # Small chance to spawn an obstacle
            print("spawn enemy")
            obstacle = world.add_entity()
            world.assign_component(obstacle, Position, Position(10, -50))
            world.assign_component(obstacle, Sprite, Sprite(ENEMY_PATH, (350, 350)))
            world.assign_component(obstacle, Velocity, Velocity(0, 10)) 

        # Update world
        movement_system(world, dt)
        scrolling_system(world, dt)
        # collision_system(world, dt)
        rendering_system(world, dt)

        # End game if health is 0
        # if world.entities_comps_data[ship][Health].hp <= 0:
        #     print("Game Over")
        #     running = False

    pygame.quit()

# # # https://lowich.itch.io/free-spaceship-sprites?download
# # # https://piiixl.itch.io/space


