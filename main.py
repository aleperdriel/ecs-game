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
SPEED = 350
SPEED_INCREMENT = 10
SPAWN_CHANCE = 0.015

# Assets loading
BG_PATH = "assets/backgrounds/Space_Stars6.png"
BG_START_PATH = "assets/backgrounds/start_blurred.png"
start_img = pygame.image.load(BG_START_PATH)

SHIP_PATH = "assets/ships/purple.png"
ASTEROID_PATH = "assets/env/asteroid.png"
ENEMY_SHIP_PATH = "assets/ships/Green.png"
ENEMY_PATH = "assets/ships/brown.png"
ENEMIES_SPRITES = [ASTEROID_PATH, ASTEROID_PATH, ASTEROID_PATH, ASTEROID_PATH, ENEMY_SHIP_PATH, ENEMY_PATH]

GAME_MUSIC = "assets/sounds/game.ogg"
START_MUSIC = "assets/sounds/start.ogg"
GO_SOUND = "assets/sounds/gameover.wav"
HIT_SOUND = "assets/sounds/playerhit.mp3"

Entity = int
Bitmask = int


class Component:
    pass

class System:
    def __call__(self, world: World, dt: float) -> None:
        pass

class Game:
    def __init__(self):
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


# ECS basic functions ---------------------------------------------------------------
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
            raise IndexError(f"The maximum of {len(self.comps)} components has been reached")
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


# Components -----------------------------------------------------------------------

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

        self.mask = pygame.mask.from_surface(self.image)

class Background(Component):
    pass

class Health(Component):
    def __init__(self, hp: int) -> None:
        self.hp = hp

class Damage(Component):
    def __init__(self, dp: int) -> None:
        self.dp = dp

class Flicker(Component):
    def __init__(self, duration: float) -> None:
        self.duration = duration

# Systems -----------------------------------------------------------------------
class MovementSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        for entity in world.query(Position, Velocity):
            pos = world.entities_comps_data[entity][Position]
            vel = world.entities_comps_data[entity][Velocity]
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt
            
            if pos.y > WINDOW_HEIGHT:
                world.remove_entity(entity)

class ScrollingSystem(System):
    def __init__(self):
        self.speed = SPEED
        self.speed_increment = SPEED_INCREMENT
    def __call__(self, world: World, dt: float) -> None:
        for entity in world.query(Position, Sprite, Background):
            pos = world.entities_comps_data[entity][Position]
            sprite = world.entities_comps_data[entity][Sprite]
            
            # Increase each second the speed
            self.speed += SPEED_INCREMENT * dt
            SPEED = self.speed
            
            pos.y += self.speed * dt
            if pos.y >= sprite.size[1]:
                pos.y -= sprite.size[1]
         
class ObsSpawnSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        if random.random() < SPAWN_CHANCE:
            obstacle = world.add_entity()
            world.assign_component(obstacle, Position, Position(random.randrange(0, WINDOW_WIDTH), -40))

            # Random size for the obstacle
            rand_size = random.randrange(64, 120)
            rand_path = random.choice(ENEMIES_SPRITES)
            world.assign_component(obstacle, Sprite, Sprite(rand_path, (rand_size, rand_size)))

            rand_velocity = random.randrange(SPEED, SPEED * 2)

            # Random velocity to the bottom of the screen
            world.assign_component(obstacle, Velocity, Velocity(0, rand_velocity))
            world.assign_component(obstacle, Damage, Damage(1))

        
class CollisionSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        
        if world.query(Position, Health):
            ship = world.query(Position, Health)[0]

            ship_pos = world.entities_comps_data[ship][Position]
            ship_sprite = world.entities_comps_data[ship][Sprite]
            ship_health = world.entities_comps_data[ship][Health]

            for obstacle in world.query(Position, Sprite, Damage):
                obs_pos = world.entities_comps_data[obstacle][Position]
                obs_sprite = world.entities_comps_data[obstacle][Sprite]

                offset = (int(obs_pos.x - ship_pos.x), int(obs_pos.y - ship_pos.y))

                # Check if the ship's sprite overlaps with the obstacle's
                if ship_sprite.mask.overlap(obs_sprite.mask, offset):
                    world.assign_component(ship, Flicker, Flicker(0.6))
                    ship_health.hp -= 1
                    world.remove_entity(obstacle)
                    if ship_health.hp != 0 : pygame.mixer.Sound(HIT_SOUND).play()


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

                if Flicker in world.entities_comps_data[entity]:
                    flicker = world.entities_comps_data[entity][Flicker]

                    # Display the sprite every two frames
                    if int(flicker.duration * 10) % 2 == 0:
                        self.screen.blit(sprite.image, (pos.x, pos.y))
                else:
                    self.screen.blit(sprite.image, (pos.x, pos.y))

        # Display health
        if len((world.query(Position, Health))) > 0:
            ship_health = world.entities_comps_data[world.query(Position, Health)[0]][Health]
            sh = ship_health.hp

        else : sh = 10
        font = pygame.font.Font(None, 36)
        health_text = font.render(f"Health Points: {sh}", True, (255, 255, 255))
        self.screen.blit(health_text, (10, 10))


        pygame.display.flip()

    def render_background(self, world: World) -> None:

        # Select only background entities
        for entity in world.query(Position, Sprite, Background):
            pos = world.entities_comps_data[entity][Position]
            sprite = world.entities_comps_data[entity][Sprite]
            
            tile_size = sprite.size[0]
            
            # Render the background with scrolling
            for i in range(0, WINDOW_HEIGHT, tile_size):
                for j in range(-tile_size, WINDOW_WIDTH + tile_size *2, tile_size):
                    self.screen.blit(sprite.image, (i, j + pos.y))

class FlickerSystem(System):
    def __call__(self, world: World, dt: float) -> None:
        for entity in world.query(Flicker):
            flicker = world.entities_comps_data[entity][Flicker]
            flicker.duration -= dt
            if flicker.duration <= 0:
                world.unassign_component(entity, Flicker)

# Screens management functions --------------------------------------
def show_start_menu(start_img):
    pygame.mixer.music.load(START_MUSIC)
    pygame.mixer.music.play(loops=-1)

    font_title = pygame.font.Font(None, 80)
    title = font_title.render(TITLE, True, (255, 255, 255))
    font_text = pygame.font.Font(None, 40)
    instructions_text = font_text.render("Press space", True, (255, 255, 255))
    second_text = font_text.render("to start the exploration", True, (255, 255, 255))

    # Start menu UI
    start_img = pygame.transform.scale(start_img, (WINDOW_HEIGHT, WINDOW_HEIGHT))

    screen.blit(start_img, (0, 0) ) 
    
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, WINDOW_HEIGHT / 2 - title.get_height()))
    screen.blit(instructions_text, (WINDOW_WIDTH / 2 - instructions_text.get_width() / 2, WINDOW_HEIGHT / 2 + 50))
    screen.blit(second_text, (WINDOW_WIDTH / 2 - second_text.get_width() / 2, WINDOW_HEIGHT / 2 + 100))

    pygame.display.flip()

    # Wait for any key press to start the game
    waiting_action = True
    while waiting_action:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if pygame.key.get_pressed() and pygame.key.get_pressed()[pygame.K_SPACE]:
                waiting_action = False
                run_game()

def show_game_over(timescore):
    pygame.mixer.music.load(GO_SOUND)
    pygame.mixer.music.play()

    font_title = pygame.font.Font(None, 80)
    title = font_title.render("GAME OVER", True, (255, 255, 255))
    font_text = pygame.font.Font(None, 40)
    instructions_text = font_text.render("Maybe the exploration", True, (255, 255, 255))
    second_text = font_text.render("was not for you...", True, (255, 255, 255))
    score = font_text.render("Score: " + timescore + "s", True, (255, 255, 255))
    restart_text = font_text.render("Press Space", True, (255, 255, 255))

    screen.fill((100, 50, 50))
    
    screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, WINDOW_HEIGHT / 2 - title.get_height()))
    screen.blit(instructions_text, (WINDOW_WIDTH / 2 - instructions_text.get_width() / 2, WINDOW_HEIGHT / 2 + 50))
    screen.blit(second_text, (WINDOW_WIDTH / 2 - second_text.get_width() / 2, WINDOW_HEIGHT / 2 + 100))
    screen.blit(score, (WINDOW_WIDTH / 2 - score.get_width() / 2, WINDOW_HEIGHT / 2 + 150))
    screen.blit(restart_text, (WINDOW_WIDTH / 2 - score.get_width() / 2, WINDOW_HEIGHT / 2 + 250))

    pygame.display.flip()

    pygame.time.wait(2000)

    # Prevent from pressing too quick
    pygame.event.clear()

    is_game_over = True
    while is_game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if pygame.key.get_pressed() and pygame.key.get_pressed()[pygame.K_SPACE]:
                run_game()

def run_game():
    world = World()

    pygame.mixer.music.load(GAME_MUSIC)
    pygame.mixer.music.play(loops=-1)

    # Define components in the world
    world.register_component(Position)
    world.register_component(Velocity)
    world.register_component(Sprite)
    world.register_component(Health)
    world.register_component(Background)
    world.register_component(Damage)
    world.register_component(Flicker)

    # Create the ship entity
    ship = world.add_entity()    
    ship_pos = Position(WINDOW_WIDTH/2 - 32, WINDOW_HEIGHT - 120)
    world.assign_component(ship, Position, ship_pos)
    world.assign_component(ship, Sprite, Sprite(SHIP_PATH, (86, 86)))
    world.assign_component(ship, Health, Health(5))

    # Create the background
    bg = world.add_entity()
    world.assign_component(bg, Position, Position(0,0))
    world.assign_component(bg, Sprite, Sprite(BG_PATH, (128, 128)))
    world.assign_component(bg, Background, Background)


    # Systems init -------------------------------------------------------------------

    movement_system = MovementSystem()
    scrolling_system = ScrollingSystem()
    collision_system = CollisionSystem()
    rendering_system = RenderingSystem(screen)
    obs_spawn_system = ObsSpawnSystem()
    flicker_system = FlickerSystem()


    # Game loop ---------------------------------------------------------------------
    running = True
    start_time = pygame.time.get_ticks()

    while running:

        # Delta time in seconds
        dt = clock.tick(60) / 1000.0  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

        # Move depending on the key pressed should it be updated with system ?
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            ship_pos.x -= SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ship_pos.x += SPEED * dt 

        # Prevent ship from leaving the screen
        ship_pos.x = max(0, min(ship_pos.x, WINDOW_WIDTH - 64))

        # Update world
        movement_system(world, dt)
        scrolling_system(world, dt)
        collision_system(world, dt)
        rendering_system(world, dt)
        obs_spawn_system(world, dt)
        flicker_system(world, dt)

        # End game if health is 0
        if world.entities_comps_data[ship][Health].hp <= 0:
            running = False
            timescore = (pygame.time.get_ticks() - start_time) / 1000
            show_game_over(str(timescore))

if __name__ == "__main__":
    pygame.init()
    
    # Sound
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    is_start_menu = True
    if is_start_menu :
        show_start_menu(start_img)
    
    pygame.quit()

