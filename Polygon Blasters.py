import pygame as pg
import math
import random

#initialize pygame
pg.init()

#Make the screen
SCREEN_WIDTH = 650
SCREEN_HEIGHT = 800
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("Polygon Blasters")
pg.display.set_icon(pg.transform.scale_by(pg.image.load("img/player.png").convert_alpha(), 0.5))

#Manage Framerate
clock = pg.time.Clock()
fps = 60

#if you ever need to place some text on the screen
def draw_text(text, font_size, color, x, y, font_type=None, antialias=True, alpha=20):
    font = pg.font.SysFont(font_type, font_size)
    img = font.render(text, antialias, color)

    img.set_alpha(alpha)

    rect = img.get_rect(center=(x, y))

    screen.blit(img, rect)

#a bunch of sfx
death_sound = pg.mixer.Sound("sfx/player_death.wav")
unfocused_player_shot = pg.mixer.Sound("sfx/player_shot-unfocused.wav")
focused_player_shot = pg.mixer.Sound("sfx/player_shot-focused.wav")
enemy_shot = pg.mixer.Sound("sfx/enemy_shot2.wav")
enemy_hit = pg.mixer.Sound("sfx/enemy_hit.wav")
graze_sfx = pg.mixer.Sound("sfx/graze_sfx.wav")
life_gained = pg.mixer.Sound("sfx/life_gained.wav")

class Shape:
    """
    a class for creating just about everything on-screen
    """
    def __init__(self, initial_x, initial_y, img, hitbox_radius):
        self.x = initial_x
        self.y = initial_y
        self.image = img
        self.width, self.height = img.get_size()
        self.hitbox_radius = hitbox_radius

    def draw(self, window):
        x_left_corner = int(self.x) - self.width // 2
        y_left_corner = int(self.y) - self.height // 2
        window.blit(self.image, (x_left_corner, y_left_corner))

    def get_center(self):
        return self.x , self.y


#a class to help me program the player
# noinspection SpellCheckingInspection
class Player(Shape):
    """
    This is actually the first class I have coded. It manages the creation & behavior of the player
    """

    #A bunch of attributes of the player
    v= 7
    v_focus = 2
    is_focused = False
    grazed_bullets = 0

    def __init__(self, initial_x, initial_y, starting_lives, graze_radius):
        Shape.__init__(self, initial_x, initial_y, pg.image.load("img/player.png").convert_alpha(), 10)
        self.lives_remaining = starting_lives
        self.bonus_life_quota = 64
        self.is_alive = True
        self.is_invulnerable = False
        self.invulnerable_until = 0
        self.last_shot_at = pg.time.get_ticks()
        self.graze_radius = graze_radius
        self.invulnerability_particles_img = pg.image.load("img/invulnerability_particles.png").convert_alpha()

    #manage keyboard input
    def check_movement(self, key):
        speed = self.v_focus if self.is_focused else self.v

        dx = 0
        dy = 0

        if key[pg.K_LEFT] and self.x > self.hitbox_radius:
            dx -= speed
        if key[pg.K_RIGHT] and self.x < SCREEN_WIDTH - self.hitbox_radius:
            dx += speed
        if key[pg.K_UP] and self.y > self.hitbox_radius:
            dy -= speed
        if key[pg.K_DOWN] and self.y < SCREEN_HEIGHT - self.hitbox_radius:
            dy += speed

        if dx != 0 and dy != 0:
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        self.x += dx
        self.y += dy

        if key[pg.K_z]:
            shot_cooldown = 100
            if pg.time.get_ticks() > self.last_shot_at + shot_cooldown:
                self.shoot()


    def shoot(self):
        if self.is_focused:
            pg.mixer.Sound.play(focused_player_shot)
            bullet_zone = 24
            for bullet_no in range(2):
                active_player_bullets.append(PlayerBullet(self.x - (bullet_zone/2) + (bullet_zone*bullet_no), self.y - 50))
        else:
            pg.mixer.Sound.play(unfocused_player_shot)
            bullet_zone = 144
            for bullet_no in range(4):
                active_player_bullets.append(PlayerBullet(self.x - (bullet_zone/2) + (bullet_zone*bullet_no)/3 , self.y - 50))

        self.last_shot_at = pg.time.get_ticks()

    #defines how to behave when k*lled(do I need to censor the word kill?)
    def die(self):
        pg.mixer.Sound.play(death_sound)
        self.lives_remaining -= 1
        if self.lives_remaining < 1:
            self.is_alive = False
        self.is_invulnerable = True
        self.invulnerable_until = pg.time.get_ticks() + 3000


#load the player bullet images
unfocused_bullet = pg.image.load("img/player_bullet.png").convert_alpha()
focus_bullet = pg.image.load("img/long_player_bullet.png").convert_alpha()

class PlayerBullet(Shape):
    def __init__(self, x, y):
        Shape.__init__(self, x, y, focus_bullet if player.is_focused else unfocused_bullet, 8)
        self.v = 16
        self.is_alive = True
        self.damage = 30 if player.is_focused else 15

    def move(self):
        self.y -= self.v


class Enemy(Shape):
    """
    this manages the creation of both popcorn enemies & bosses
    """

    def __init__(self, initial_coods, archetype):
        data = enemy_archetypes[archetype]

        Shape.__init__(self, initial_coods[0], initial_coods[1], data["design"], data["hitbox"])
        self.initial_coods = initial_coods
        self.hp_remaining = data["hp"]
        self.was_grazed = False
        self.type = archetype
        self.hitbox_radius = data["hitbox"]
        self.hurtbox_radius = data["hurtbox"]
        self.base_image = data["design"]
        self.image = data["design"]
        self.angle = 0
        self.spin_speed = 3

    def draw(self, window):
        rotated = pg.transform.rotate(self.base_image, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        window.blit(rotated, rect.topleft)


#these are the functions that describe the creation of enemy bullet patterns
#just about all the code for the patterns is AI generated

#to spawn homing bullets
def shoot_aimed(enemy, bullet_type, speed):
    x_component = player.x - enemy.x
    y_component = player.y - enemy.y

    dist = (x_component**2 + y_component**2)**0.5
    if dist == 0:
        return

    vx = speed * x_component / dist
    vy = speed * y_component / dist

    #an error occurs whenever the player is directly under the enemy since vx becomes 0
    try:
        angle = math.degrees(math.atan(vy / vx))

    except ZeroDivisionError:
        angle = 0

    pg.mixer.Sound.play(enemy_shot)
    active_bullets.append(Bullet(bullet_type, enemy.x, enemy.y, vx, vy, angle=angle))

#shoots 3 homing bullets
def shoot_line(enemy):
    if current_time < enemy.next_shot_at:
        return

    if enemy.burst_step < 3:
        shoot_aimed(enemy, "red orb", 8)
        enemy.burst_step += 1
        enemy.next_shot_at = current_time + enemy.shot_interval
    else:
        enemy.burst_step = 0
        enemy.next_shot_at = current_time + enemy.attack_cooldown

def shoot_spread(enemy, bullet_type, base_angle, count, angle_step, speed):

    for i in range(count):
        angle = base_angle + (i - (count - 1) / 2) * angle_step

        rad = math.radians(angle)

        vx = math.cos(rad) * speed
        vy = math.sin(rad) * speed

        pg.mixer.Sound.play(enemy_shot)
        active_bullets.append(
            Bullet(bullet_type, enemy.x, enemy.y, vx, vy, angle-90)
        )

#shoots the arch that tetraman uses
def shoot_arch(enemy):
    if current_time < enemy.next_shot_at:
        return

    dx = player.x - enemy.x
    dy = player.y - enemy.y

    base_angle = math.degrees(math.atan2(dy, dx))

    for step in range(4):
        shoot_spread(enemy, "big orb",(base_angle+(90*step)), 4, 15, 5)
    enemy.next_shot_at = current_time + enemy.attack_cooldown

#shoots the reverse pyramids that pentess uses
def shoot_pyramid(enemy):

    if current_time < enemy.next_shot_at:
        return

    dx = player.x - enemy.x
    dy = player.y - enemy.y

    base_angle = math.degrees(math.atan2(dy, dx))

    if enemy.burst_step <= 4:

        for step in range(4):
            shoot_spread(
                enemy,
                "yellow rice",
                base_angle= base_angle + (90*step),
                count=enemy.burst_step + 1,
                angle_step=25,
                speed=3
            )

        enemy.burst_step += 1
        enemy.next_shot_at = current_time + enemy.shot_interval

    else:
        enemy.burst_step = 0
        enemy.next_shot_at = current_time + enemy.attack_cooldown

def shoot_spiral(enemy):

    if current_time < enemy.next_shot_at:
        return

    shoot_spread(
        enemy,
        "green orb",
        base_angle=enemy.spiral_angle,
        count=6,
        angle_step=60,
        speed=5
    )

    enemy.spiral_angle += 36
    enemy.next_shot_at = current_time + enemy.shot_interval

#this describes the enemy archetypes
enemy_archetypes = {
    "triman": {
        "design": pg.image.load("img/triman.png").convert_alpha(),
        "hp": 120,
        "pattern": shoot_line,
        "shot interval": 120,
        "attack cooldown": 600,
        "hitbox": 36,
        "hurtbox": 20,
        "reward":1
    },
    "tetraman": {
        "design": pg.image.load("img/tetraman.png").convert_alpha(),
        "hp": 250,
        "pattern": shoot_arch,
        "shot interval": 125,
        "attack cooldown": 1500,
        "hitbox": 36,
        "hurtbox": 20,
        "reward":1
    },
    "pentess": {
        "design": pg.image.load("img/pentess.png").convert_alpha(),
        "hp": 500,
        "pattern": shoot_pyramid,
        "shot interval": 100,
        "attack cooldown": 900,
        "hitbox": 40,
        "hurtbox": 20,
        "reward":3
    },
    "hexman": {
        "design": pg.image.load("img/hexman.png").convert_alpha(),
        "hp": 2400,
        "pattern": shoot_spiral,
        "shot interval": 75,
        "attack cooldown": 800,
        "hitbox": 45,
        "hurtbox": 25,
        "reward":5
    }
}

#this describes some common spawn points enemies will be spawning at
spawn_points = ((0, SCREEN_HEIGHT * 0.2), (SCREEN_WIDTH * 0.1, -20), (SCREEN_WIDTH * 0.3, -20),
(SCREEN_WIDTH * 0.5, -20), (SCREEN_WIDTH * 0.7, -20), (SCREEN_WIDTH * 0.9, -20), (SCREEN_WIDTH, SCREEN_HEIGHT * 0.2))

class Henchman(Enemy):
    """
    A class to manage the popcorn enemies' behavior & spawning
    """

    def __init__(self, archetype, initial_coods, entry_time, mid_coods, exit_time, final_coods, delay=0, rest_time=0):
        data = enemy_archetypes[archetype]
        Enemy.__init__(self, initial_coods, archetype)
        self.is_alive = True
        self.state = "enter"
        self.spawn_time = pg.time.get_ticks()
        self.entry_time = entry_time
        self.mid_coods = mid_coods
        self.exit_time = exit_time
        self.final_coods = final_coods
        self.delay = delay
        self.rest_time = rest_time
        self.pattern = data["pattern"]
        self.burst_step = 0
        self.last_shot = self.spawn_time
        self.shot_interval = data["shot interval"]
        self.attack_cooldown = data["attack cooldown"]
        self.next_shot_at = self.spawn_time
        self.spiral_angle = 0
        self.rewards_amount = data["reward"]

    def move(self):
        #figure out how long the enemy has been alive
        elapsed = pg.time.get_ticks() - self.spawn_time

        #while at the "enter" or "exit" stage, teleport the enemy into the location they should be at
        if self.state == "enter":
            progress = elapsed / self.entry_time
            progress = min(progress, 1)    #don't allow progress to exceed the value of 1

            self.x = self.initial_coods[0] + ((self.mid_coods[0] - self.initial_coods[0]) * progress)
            self.y = self.initial_coods[1] + ((self.mid_coods[1] - self.initial_coods[1]) * progress)
            self.angle += self.spin_speed   #spin the enemy

            if progress >= 1:
                #once the enemy has finished entering, switch to the pause phase
                self.state = "pause"
                if self.rest_time != 0:
                    self.angle = 0
        elif self.state == "pause":
            if elapsed >= self.entry_time + self.rest_time:
                #don't move until rest_time is over. Then switch to the exit phase
                self.state = "exit"
        elif self.state == "exit":
            #same algorithm as the enter phase with some variables changed
            progress = (elapsed - self.entry_time - self.rest_time) / self.exit_time
            progress = min(progress, 1)

            self.x = self.mid_coods[0] + ((self.final_coods[0] - self.mid_coods[0]) * progress)
            self.y = self.mid_coods[1] + ((self.final_coods[1] - self.mid_coods[1]) * progress)
            self.angle += self.spin_speed

            if progress >= 1:
                #despawn enemy once it has completed its algorithm
                self.is_alive = False

    def shoot(self):
        self.pattern(self)


#this helps with defining the types of bullets
bullet_types = {
    "red orb": {"hitbox": 13, "design": pg.image.load("img/red orb.png").convert_alpha()},
    "green orb": {"hitbox": 13, "design": pg.image.load("img/green orb.png").convert_alpha()},
    "big orb": {"hitbox": 18, "design": pg.image.load("img/big orb.png").convert_alpha()},
    "yellow rice": {"hitbox": 9, "design": pg.image.load("img/yellow rice.png").convert_alpha()}
}

class Bullet(Shape):
    def __init__(self, archetype, x, y, vx, vy, angle=0):
        data = bullet_types[archetype]
        design = pg.transform.rotate(data["design"], angle)
        Shape.__init__(self, x, y, design, data["hitbox"])
        self.was_grazed = False
        self.is_alive = True
        self.vx = vx
        self.vy = vy


points_img = pg.image.load("img/point particle.png").convert_alpha()
class PointParticles(Shape):
    def __init__(self, x, y):
        Shape.__init__(self, x, y, points_img, 32)
        self.x = x
        self.y = y
        self.vy = 8
        self.attraction_dist = 100
        self.was_grabbed = False

    def update(self):
        delta_y = player.y - self.y
        delta_x = player.x - self.x

        dist = (delta_x**2 + delta_y**2)**0.5
        if dist <= self.attraction_dist and dist != 0:
            dir_x = delta_x / dist
            dir_y = delta_y / dist

            attraction_speed = 7

            self.x += attraction_speed * dir_x
            self.y += attraction_speed * dir_y
        else:
            self.y += self.vy


class DeathRing:
    def __init__(self, x, y, radius= 2):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = 50
        self.alpha = 0
        self.ring_surface = pg.Surface((128, 128), pg.SRCALPHA)
        self.color = [random.randint(128, 255), random.randint(0, 128), 0, self.alpha]


# create player
player = Player((SCREEN_WIDTH / 2), SCREEN_HEIGHT - 150, 3, 45)


#Track objects
score = 0
last_spawn_time = 0
spawn_queue = []
active_enemies = []
active_bullets = []
active_player_bullets = []
point_particles = []
point_particles_collected = 0
death_rings = []  # not sure if this is worth an entire list ,but I couldn't come up with anything better


#the following are some useful functions to spawn enemies in certain patterns

#the following spawns only a single enemy
#This just saves me the trouble of dealing with too many parentheses
# noinspection PyDefaultArgument
def spawn_henchman(archetype, initial_coods, entry_time, mid_coods, exit_time,
                   final_coods, delay=0, rest_time=0, enemy_list=None):

    if enemy_list is None:
        enemy_list = spawn_queue

    enemy_list.append(Henchman(
        archetype, initial_coods, entry_time, mid_coods, exit_time, final_coods, delay=delay,rest_time=rest_time
    ))

#spawns a line of duplicated enemies
# noinspection PyDefaultArgument
def spawn_line(archetype, initial_coods, mid_coods, final_coods, travel_time,
               count, line_delay=0, enemy_delay = None, rest_time = 0, enemy_list=None):

    if enemy_list is None:
        enemy_list = spawn_queue

    #this sets it to the default delay which I like
    if enemy_delay is None:
        enemy_delay = int((travel_time / 3000) * 350)


    entry_distance = ((initial_coods[1] - mid_coods[1]) ** 2 + (initial_coods[0] - mid_coods[0]) ** 2)**0.5
    exit_distance = ((mid_coods[1] - final_coods[1]) ** 2 + (mid_coods[0] - final_coods[0]) ** 2)**0.5
    total_distance = entry_distance + exit_distance

    #calculate entry and exit time
    entry_time = travel_time*(entry_distance/total_distance)
    exit_time = travel_time*(exit_distance/total_distance)

    #this decides how long to wait before spawning the line
    enemy_list.append(Henchman(archetype, initial_coods, entry_time, mid_coods, exit_time, final_coods,
                               delay=line_delay, rest_time=rest_time))
    count -= 1

    #this will spawn the rest of the line
    while count > 0:
        enemy_list.append(Henchman(
            archetype, initial_coods, entry_time, mid_coods, exit_time, final_coods,
            delay=enemy_delay, rest_time=rest_time))
        count -= 1

#this spawns 5 enemies of the same type in a slanted line from one end of the screen till the other
#you can make multiple slanted lines using lines_no to form zigzag lines
# noinspection PyDefaultArgument
def spawn_slant_line(archetype, start_point, descent_time, lines_no=1, spawn_delay= 0, enemy_list=None):

    if enemy_list is None:
        enemy_list = spawn_queue

    #calculate entry and exit times
    entry_time = descent_time*0.2
    exit_time = descent_time*0.8

    #this will figure out the spacing between the enemies
    enemy_delay = (SCREEN_HEIGHT/descent_time)*1500

    #wait till spawn_delay is over to start making the pattern
    enemy_list.append(Henchman(archetype, start_point, entry_time, (start_point[0], SCREEN_HEIGHT * 0.2), exit_time,
                               (start_point[0], SCREEN_HEIGHT), delay=spawn_delay))
    #generate the rest of the line
    if start_point[0] == SCREEN_WIDTH*0.1:
        for i in range(1, 4+1):
            spawn_point_x = start_point[0] + (i*SCREEN_WIDTH*0.2)
            enemy_list.append(Henchman(archetype, (spawn_point_x, -20), entry_time, (spawn_point_x, SCREEN_HEIGHT * 0.2),
                                       exit_time, (spawn_point_x, SCREEN_HEIGHT), delay=enemy_delay))
    elif start_point[0] == SCREEN_WIDTH*0.9:
        for i in range(1, 4+1):
            spawn_point_x = start_point[0] - (i * SCREEN_WIDTH * 0.2)
            enemy_list.append(Henchman(archetype, (spawn_point_x, -20), entry_time, (spawn_point_x, SCREEN_HEIGHT * 0.2),
                                       exit_time, (spawn_point_x, SCREEN_HEIGHT), delay=enemy_delay))
    lines_no -= 1

    #generate the rest of the slanted lines
    starting_x = start_point[0]
    while lines_no > 0:
        if starting_x == SCREEN_WIDTH*0.1:
            for i in range(3, -1, -1):
                spawn_point_x = starting_x + (i * SCREEN_WIDTH*0.2)
                enemy_list.append(Henchman(archetype, (spawn_point_x, -20), entry_time, (spawn_point_x, SCREEN_HEIGHT * 0.2),
                                           exit_time, (spawn_point_x, SCREEN_HEIGHT), delay=enemy_delay))
            starting_x = SCREEN_WIDTH*0.9
        elif starting_x == SCREEN_WIDTH*0.9:
            for i in range(3, -1, -1):
                spawn_point_x = starting_x - (i * SCREEN_WIDTH*0.2)
                enemy_list.append(Henchman(archetype, (spawn_point_x, -20), entry_time, (spawn_point_x, SCREEN_HEIGHT * 0.2),
                                           exit_time, (spawn_point_x, SCREEN_HEIGHT), delay=enemy_delay))
            starting_x = SCREEN_WIDTH * 0.1
        lines_no -= 1


# noinspection PyDefaultArgument
def spawn_top_row(archetype, descent_time, rest_time, count, spawn_delay, enemy_list=None):

    if enemy_list is None:
        enemy_list = spawn_queue

    # calculate entry and exit time
    entry_time = descent_time * 0.2
    exit_time = descent_time * 0.8

    enemy_list.append(Henchman(
        archetype, (int(SCREEN_WIDTH / (count + 1)), -20), entry_time, (int(SCREEN_WIDTH / (count + 1)), SCREEN_HEIGHT * 0.2),
        exit_time, (int(SCREEN_WIDTH/(count+1)), SCREEN_HEIGHT), rest_time = rest_time ,delay=spawn_delay))
    enemies_spawned = 1

    while enemies_spawned < count:
        enemies_spawned += 1
        spawn_point_x = int(SCREEN_WIDTH * enemies_spawned / (count + 1))
        enemy_list.append(Henchman(
            archetype, (spawn_point_x, -20), entry_time, (spawn_point_x, SCREEN_HEIGHT * 0.2),
            exit_time, (spawn_point_x, SCREEN_HEIGHT), rest_time = rest_time))


#this is where all enemies are created. change it if you want more/fewer enemies
def create_stage():
    spawn_line("triman", spawn_points[1], (SCREEN_WIDTH*0.1, SCREEN_HEIGHT*0.2),
    spawn_points[6], 3000, 10, line_delay = 3000)
    spawn_line("triman", spawn_points[5], (SCREEN_WIDTH*0.9, SCREEN_HEIGHT * 0.2),
    spawn_points[0], 3000, 10)

    spawn_top_row("tetraman", 8000, 6500, 8, 2000)

    spawn_slant_line("triman", spawn_points[5], 2500, spawn_delay=7000, lines_no=5)

    spawn_line("triman", spawn_points[6], (SCREEN_WIDTH*0.9, SCREEN_HEIGHT*0.2), spawn_points[0],
    3500, 10, line_delay = 4000)
    spawn_top_row("tetraman", 2000, 7000, 3, 0)
    spawn_line("triman", spawn_points[6], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2), spawn_points[6],
    3500, 10)

    spawn_top_row("pentess", 3000, 15000, 5, 4500)

    spawn_line("triman", spawn_points[0], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2), spawn_points[6],
               3500, 10, line_delay=12000)
    spawn_top_row("tetraman", 2000, 7000, 3, 0)
    spawn_line("triman", spawn_points[6], (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2), spawn_points[0],
               3500, 10)

    spawn_slant_line("triman", spawn_points[1], 2500, spawn_delay=6000, lines_no=5)

    spawn_top_row("pentess", 2500, 15000, 3, 5000)
    spawn_line("tetraman", spawn_points[0], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2), spawn_points[0],
               2000, 1, line_delay=1500, rest_time=10000)
    spawn_line("tetraman", spawn_points[6], (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2), spawn_points[6],
               2000, 1, line_delay=1500, rest_time=10000)

    spawn_line("triman", spawn_points[6], (SCREEN_WIDTH*0.9, SCREEN_HEIGHT*0.2),
               spawn_points[0], 3000, 8, line_delay=12000)
    spawn_line("triman", spawn_points[0], (SCREEN_WIDTH*0.1, SCREEN_HEIGHT * 0.2),
               spawn_points[6], 3000, 8)

    spawn_henchman("hexman", (SCREEN_WIDTH/3, -20), 2000,
    (SCREEN_WIDTH/3 ,SCREEN_HEIGHT * 0.2), 6000, (SCREEN_WIDTH/3 ,SCREEN_HEIGHT),
    delay=4000, rest_time=25000)
    spawn_henchman("hexman", (SCREEN_WIDTH/2, -20), 2000,
    (SCREEN_WIDTH/2, SCREEN_HEIGHT * 0.2), 6000, (SCREEN_WIDTH/2, SCREEN_HEIGHT),
    delay=1200, rest_time=25000)
    spawn_henchman("hexman", (SCREEN_WIDTH*2/3, -20), 2000,
    (SCREEN_WIDTH*2 / 3, SCREEN_HEIGHT * 0.2), 6000, (SCREEN_WIDTH*2 / 3, SCREEN_HEIGHT),
    delay=1200, rest_time=25000)

    spawn_line("triman", spawn_points[0], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2),
    spawn_points[6], 3000, 8, line_delay=21000)
    spawn_line("triman", spawn_points[6], (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2),
    spawn_points[0], 3000, 8)

    spawn_top_row("hexman", 8000, 12000, 1, spawn_delay=4000)
    spawn_line("tetraman", (SCREEN_WIDTH, SCREEN_HEIGHT / 2), (SCREEN_WIDTH * 0.8, SCREEN_HEIGHT / 2),
               (0, SCREEN_HEIGHT / 2), 5000, 3, line_delay=2000)
    spawn_line("tetraman", (0, SCREEN_HEIGHT / 2), (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT / 2),
               (SCREEN_WIDTH, SCREEN_HEIGHT / 2), 3500, 3)

    spawn_line("tetraman", spawn_points[0], (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.2), spawn_points[6],
               5000, 4, line_delay=3500)
    spawn_line("tetraman", spawn_points[6], (SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.2), spawn_points[0],
               5000, 4)

    spawn_slant_line("triman", spawn_points[5], 2500, spawn_delay=5000, lines_no=5)

    spawn_top_row("pentess", 2500, 15000, 3, 5600)
    spawn_line("tetraman", spawn_points[0], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2), spawn_points[0],
               2000, 1, line_delay=1500, rest_time=10000)
    spawn_line("tetraman", spawn_points[6], (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2), spawn_points[6],
               2000, 1, line_delay=1500, rest_time=10000)

    spawn_top_row("hexman", 8000, 25000, 1, spawn_delay=12000)
    spawn_line("pentess", spawn_points[0], (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2), spawn_points[6],
               8000, 3, line_delay=2500)
    spawn_line("pentess", spawn_points[6], (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2), spawn_points[0],
               8000, 3, line_delay=3500)

create_stage()

def reset_game():
    global player, score, last_spawn_time
    global spawn_queue, active_enemies, active_bullets
    global active_player_bullets, point_particles
    global point_particles_collected, death_rings

    player = Player((SCREEN_WIDTH / 2), SCREEN_HEIGHT - 150, 3, 45)

    spawn_queue = []
    active_enemies = []
    active_bullets = []
    active_player_bullets = []
    point_particles = []
    point_particles_collected = 0
    death_rings = []

    score = 0
    last_spawn_time = current_time

    create_stage()


#create a bunch of surfaces before the loop to avoid unnecessary code

#death overlay
death_overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
death_overlay.fill((0, 0, 0))
death_overlay.set_alpha(120)
#graze surface
graze_surface = pg.Surface((player.graze_radius*2, player.graze_radius*2), pg.SRCALPHA)


running = True
while running:
    # keep framerate consistent
    clock.tick(fps)

    #Keep the color of the background consistent
    screen.fill((39, 39, 39))

    current_time = pg.time.get_ticks()
    game_over = (not player.is_alive) or (len(spawn_queue) == 0 and len(active_enemies) == 0)

    if pg.time.get_ticks() >= player.invulnerable_until:
        player.is_invulnerable = False

    #draw the player unless in death animation
    if player.is_invulnerable:
        if ((current_time // 100) % 2 == 0) and (current_time < player.invulnerable_until - 2000):
            player.draw(screen)
            screen.blit(player.invulnerability_particles_img,(player.x - player.width / 2, player.y - player.height / 2))
        elif not ((current_time // 100) % 2 == 0) and (current_time < player.invulnerable_until - 2000):
            pass
        else:
            player.draw(screen)
            screen.blit(player.invulnerability_particles_img, (player.x - player.width / 2, player.y - player.height / 2))
    else:
        player.draw(screen)

    if player.is_alive:
        # check keyboard for input
        keys = pg.key.get_pressed()

        #allow the player to restart
        if keys[pg.K_r] and keys[pg.K_LCTRL]:
            reset_game()

        #if the player is pressing shift, enter focus mode
        if keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]:
            player.is_focused = True

            #display the hitbox
            pg.draw.circle(screen,(0,255,0), player.get_center(), player.hitbox_radius)

            #display the grazing zone
            pg.draw.circle(graze_surface, (255, 0, 0, 35), (player.graze_radius,player.graze_radius), player.graze_radius)
            screen.blit(graze_surface,(player.x - player.graze_radius, player.y - player.graze_radius))
        else:
            player.is_focused = False

        #move the player
        player.check_movement(keys)

        #add some enemies
        if spawn_queue:
            next_enemy = spawn_queue[0]

            if current_time - last_spawn_time >= next_enemy.delay:
                next_enemy.spawn_time = current_time  # reset baseline for movement
                next_enemy.last_shot = current_time
                next_enemy.next_shot_at = current_time + next_enemy.entry_time
                next_enemy.burst_step = 0
                active_enemies.append(next_enemy)
                last_spawn_time = current_time
                spawn_queue.pop(0)

    for henchman in active_enemies:
        henchman.draw(screen)
        if player.is_alive:
            henchman.move()
            henchman.shoot()

    if not player.is_alive:
        screen.blit(death_overlay, (0, 0))
        draw_text("YOU DIED!", 96, (252, 40, 3), SCREEN_WIDTH*0.5, SCREEN_HEIGHT*0.5, alpha=255)

        if current_time >= player.invulnerable_until:
            if (current_time // 400) % 2 == 0:
                draw_text("PRESS Z TO REPLAY", 42, (255, 255, 255),
                          SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.65, alpha=255)

    #despawn dead enemies
    active_enemies = [enemy for enemy in active_enemies if enemy.is_alive]

    if player.is_alive:
        if not player.is_invulnerable:
            # check the distance between the centers of the player and each enemy
            # if they're less than player.hitbox_radius+enemy.hitbox_radius
            # then a collision has occurred and the player dies
            for enemy in active_enemies:
                dx = enemy.x - player.x
                dy = enemy.y - player.y
                graze_zone = enemy.hurtbox_radius + player.graze_radius
                hurtbox_sum = enemy.hurtbox_radius + player.hitbox_radius

                if dx * dx + dy * dy < hurtbox_sum * hurtbox_sum:
                    player.die()
                    score -= 1000 if score > 1000 else score
                elif (dx * dx + dy * dy <= graze_zone * graze_zone) and not enemy.was_grazed:
                    pg.mixer.Sound.play(graze_sfx)
                    player.grazed_bullets += 1
                    enemy.was_grazed = True
                    score += 20

        for bullet in active_bullets:
            if 0 < bullet.x < SCREEN_WIDTH and 0 < bullet.y < SCREEN_HEIGHT:
                bullet.x += bullet.vx
                bullet.y += bullet.vy

                bullet.draw(screen)
            else:
                bullet.is_alive = False

            if not player.is_invulnerable:
                dx = bullet.x - player.x
                dy = bullet.y - player.y
                radius_sum = bullet.hitbox_radius + player.hitbox_radius
                grazing_radius = bullet.hitbox_radius + player.graze_radius

                if dx * dx + dy * dy < radius_sum * radius_sum:
                    player.die()
                    score -= 1000 if score > 1000 else score
                elif (dx * dx + dy * dy < grazing_radius * grazing_radius) and not bullet.was_grazed:
                    pg.mixer.Sound.play(graze_sfx)
                    player.grazed_bullets += 1
                    bullet.was_grazed = True
                    score += 20
        active_bullets = [bullet for bullet in active_bullets if bullet.is_alive]

        for bullet in active_player_bullets:
            if bullet.y > 0:
                bullet.draw(screen)
                bullet.move()
            else:
                bullet.is_alive = False

            # check if any of the player's bullets collided with an enemy
            for enemy in active_enemies:
                dx = enemy.x - bullet.x
                dy = enemy.y - bullet.y
                radius_sum = enemy.hitbox_radius + bullet.hitbox_radius

                if dx * dx + dy * dy < radius_sum * radius_sum:
                    pg.mixer.Sound.play(enemy_hit)
                    enemy.hp_remaining -= bullet.damage
                    bullet.is_alive = False
                    score += 5
                    #if the below statement sounds weird, there was a bug where
                    #enemies spawned 2 points instead of one. The "and" fixed it.
                    if enemy.hp_remaining <= 0 and enemy.is_alive != False:
                        enemy.is_alive = False
                        death_rings.append(DeathRing(enemy.x, enemy.y))
                        for __ in range(enemy.rewards_amount):
                            x_offset = random.randint(-25, 25)
                            y_offset = random.randint(-25, 25)
                            point_particles.append(PointParticles(enemy.x+x_offset, enemy.y+y_offset))

        #despawn all bullets that aren't needed anymore
        active_player_bullets = [bullet for bullet in active_player_bullets if bullet.is_alive]

        for particle in point_particles:
            particle.draw(screen)
            particle.update()

            dx = particle.x - player.x
            dy = particle.y - player.y

            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 25:
                score += 100
                point_particles_collected += 1
                if point_particles_collected%player.bonus_life_quota == 0:
                    player.lives_remaining += 1
                    pg.mixer.Sound.play(life_gained)
                particle.was_grabbed = True
            point_particles = [particle for particle in point_particles if not particle.was_grabbed]

        for ring in death_rings:
            if ring.radius < ring.max_radius:
                ring.radius += 8
                ring.alpha += 255/6
                ring.color[3] = ring.alpha
                pg.draw.circle(ring.ring_surface, tuple(ring.color),(50, 50), ring.radius, width = 10)
                screen.blit(ring.ring_surface, (ring.x - 50, ring.y - 50))
            else:
                death_rings.remove(ring)

    # first elements of a GUI
    draw_text(f"SCORE: {score:04d}", 48, (0,255,255), 116, SCREEN_HEIGHT-15)
    draw_text(f"Graze: {player.grazed_bullets:03d}", 24, (255, 255, 255), 50, SCREEN_HEIGHT - 40)
    draw_text(f"Lives: {player.lives_remaining}", 24, (255, 255, 255), SCREEN_WIDTH-32, SCREEN_HEIGHT - 10)
    draw_text(f"Points: {point_particles_collected}/{((point_particles_collected//player.bonus_life_quota)*player.bonus_life_quota)+player.bonus_life_quota}",
    24,(255, 255, 255), 156, SCREEN_HEIGHT - 40)
    #draw_text(f"{clock.get_fps():.2f}", 50, (255, 255, 0), SCREEN_WIDTH - 50, SCREEN_HEIGHT - 20)

    if len(spawn_queue) == 0 and len(active_enemies) == 0:
        draw_text("YOU WON!!!", 96, (0,255,0), SCREEN_WIDTH/2, SCREEN_HEIGHT/2, alpha=255)

        if current_time >= last_spawn_time + 3000:
            if (current_time // 400) % 2 == 0:
                draw_text("PRESS Z TO REPLAY", 42, (255, 255, 255),
                          SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.65, alpha=255)

    #check if the player ended the game
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_z:
                if not player.is_alive:
                    if current_time >= player.invulnerable_until:
                        reset_game()

                elif len(spawn_queue) == 0 and len(active_enemies) == 0:
                    if current_time >= last_spawn_time:
                        reset_game()

    #update the screen
    pg.display.update()

pg.quit()

"""
As for how AI was used, it was a tool. I often asked it how to implement a feature 
and describe how I wanted things to work. All the code here was written and designed
by me other than the following:

    -Some math formulas such as collision checks, and specifying how to rotate and aim bullets.
    -Help in making sure enemy delay worked properly 
    -The attraction algorithm for point particles
    -Replay functionality
    -Bullet patterns
"""