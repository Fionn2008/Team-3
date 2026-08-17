import math
import pygame
import sys
from os.path import join
from random import randint, choice

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
pygame.init()

# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spiderman - Far From Dublin")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_HEALTH   = 100
HEART_DAMAGE = 5

GROUND_TOP = 490

ATTACK_COOLDOWN     = 500
enemy_ATTACK_RANGE  = 120
spider_ATTACK_RANGE = 200

SHOOT_COOLDOWN   = 1800
PROJECTILE_SPEED = 6
PROJECTILE_SIZE  = 30

NUM_COLLECTIBLES = 3
RESPAWN_DELAY    = 3000

# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
player_health = MAX_HEALTH
enemy_health  = MAX_HEALTH

player_last_attack = 0
enemy_last_attack  = 0
enemy_last_shot    = 0

score = 0

# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
bg_img = pygame.image.load(join("image", "image", "SS.FR.png")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

_raw       = pygame.image.load(join("image", "image", "spider.png")).convert_alpha()
_r         = _raw.get_bounding_rect()
player_img = pygame.transform.scale(_raw.subsurface(_r).copy(), (100, 100))

_raw      = pygame.image.load(join("image", "image", "gg.png")).convert_alpha()
_r        = _raw.get_bounding_rect()
enemy_img = pygame.transform.scale(_raw.subsurface(_r).copy(), (100, 100))

proj_green_img = pygame.image.load(join("image", "image", "green.png")).convert_alpha()
proj_green_img = pygame.transform.scale(proj_green_img, (PROJECTILE_SIZE, PROJECTILE_SIZE))

proj_red_img = pygame.image.load(join("image", "image", "red.png")).convert_alpha()
proj_red_img = pygame.transform.scale(proj_red_img, (PROJECTILE_SIZE, PROJECTILE_SIZE))

collectible_img = pygame.image.load(join("image", "image", "CFR.png")).convert_alpha()
collectible_img = pygame.transform.scale(collectible_img, (40, 40))

# ---------------------------------------------------------------------------
# Character positions
# ---------------------------------------------------------------------------
player_size  = 100
player_speed = 5
player_x     = 400
player_y     = GROUND_TOP

enemy_size  = 100
enemy_speed = 5
enemy_x     = 900
enemy_y     = GROUND_TOP

# ---------------------------------------------------------------------------
# Collectibles
# ---------------------------------------------------------------------------
def spawn_collectible():
    return {
        'x':      randint(50, SCREEN_WIDTH - 90),
        'y':      randint(GROUND_TOP, SCREEN_HEIGHT - 90),
        'active': True,
        'timer':  0,
        'phase':  randint(0, 100)
    }

collectibles = [spawn_collectible() for _ in range(NUM_COLLECTIBLES)]

# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------
projectiles = []

# ---------------------------------------------------------------------------
# Fonts & helpers
# ---------------------------------------------------------------------------
ui_font = pygame.font.SysFont(None, 24)

def draw_health_bar(x, y, health, name):
    bar_w = 100
    bar_h = 12
    fill  = int(bar_w * (health / MAX_HEALTH))
    pygame.draw.rect(screen, (255,   0, 0), (x, y - 20, bar_w, bar_h))
    pygame.draw.rect(screen, (  0, 255, 0), (x, y - 20, fill,  bar_h))
    pygame.draw.rect(screen, (  0,   0, 0), (x, y - 20, bar_w, bar_h), 2)
    label = ui_font.render(f"{name}: {health} HP", True, (255, 255, 255))
    screen.blit(label, (x, y - 40))

def get_distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
clock     = pygame.time.Clock()
game_over = False
distance  = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    now = pygame.time.get_ticks()

    if not game_over:

        # Spider-Man: A/D only, locked to ground
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            player_x -= player_speed
        if keys[pygame.K_d]:
            player_x += player_speed

        player_x = max(0, min(player_x, SCREEN_WIDTH - player_size))
        player_y = GROUND_TOP

        # Goblin auto-chases horizontally
        dx       = player_x - enemy_x
        distance = get_distance(player_x, player_y, enemy_x, enemy_y)
        if distance > 20:
            enemy_x += (dx / distance) * (enemy_speed * 0.4)

        enemy_x = max(0, min(enemy_x, SCREEN_WIDTH - enemy_size))
        enemy_y = GROUND_TOP

        # Collectibles
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        for c in collectibles:
            if c['active']:
                float_y          = c['y'] + math.sin((now / 200.0) + c['phase']) * 8
                collectible_rect = pygame.Rect(c['x'], float_y, 40, 40)
                if player_rect.colliderect(collectible_rect):
                    score         += 10
                    player_health  = min(MAX_HEALTH, player_health + 5)  # +5 HP
                    c['active']    = False
                    c['timer']     = now
            else:
                if now - c['timer'] > RESPAWN_DELAY:
                    c['x']      = randint(50, SCREEN_WIDTH - 90)
                    c['y']      = randint(GROUND_TOP, SCREEN_HEIGHT - 90)
                    c['active'] = True

        # Goblin shoots projectile every 1.8s
        if now - enemy_last_shot > SHOOT_COOLDOWN:
            enemy_last_shot = now
            ex = enemy_x + enemy_size // 2
            ey = enemy_y + enemy_size // 2
            px = player_x + player_size // 2
            py = player_y + player_size // 2
            d  = get_distance(ex, ey, px, py)
            if d > 0:
                projectiles.append({
                    'x':   ex - PROJECTILE_SIZE // 2,
                    'y':   ey - PROJECTILE_SIZE // 2,
                    'vx':  ((px - ex) / d) * PROJECTILE_SPEED,
                    'vy':  ((py - ey) / d) * PROJECTILE_SPEED,
                    'img': choice([proj_green_img, proj_red_img])
                })

        # Move projectiles, deal -5 HP on hit
        alive = []
        for p in projectiles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            proj_rect = pygame.Rect(p['x'], p['y'], PROJECTILE_SIZE, PROJECTILE_SIZE)
            if player_rect.colliderect(proj_rect):
                player_health = max(0, player_health - HEART_DAMAGE)
            elif 0 <= p['x'] <= SCREEN_WIDTH and 0 <= p['y'] <= SCREEN_HEIGHT:
                alive.append(p)
        projectiles = alive

        # Goblin melee
        if distance < enemy_ATTACK_RANGE and now - enemy_last_attack > ATTACK_COOLDOWN:
            enemy_last_attack = now
            player_health = max(0, player_health - HEART_DAMAGE)

        # Spider-Man melee on left click
        if pygame.mouse.get_pressed()[0] and now - player_last_attack > ATTACK_COOLDOWN:
            player_last_attack = now
            if distance < spider_ATTACK_RANGE:
                enemy_health = max(0, enemy_health - HEART_DAMAGE)

        if player_health <= 0 or enemy_health <= 0:
            game_over = True

    # Drawing
    screen.blit(bg_img, (0, 0))

    for c in collectibles:
        if c['active']:
            float_y = c['y'] + math.sin((now / 200.0) + c['phase']) * 8
            screen.blit(collectible_img, (c['x'], float_y))

    for p in projectiles:
        screen.blit(p['img'], (int(p['x']), int(p['y'])))

    screen.blit(player_img, (player_x, player_y))
    screen.blit(enemy_img,  (enemy_x,  enemy_y))

    if pygame.mouse.get_pressed()[0] and now - player_last_attack < 150 and distance < spider_ATTACK_RANGE:
        pygame.draw.line(screen, (255, 255, 255),
                         (player_x + 50, player_y + 50),
                         (enemy_x  + 50, enemy_y  + 50), 3)

    draw_health_bar(player_x, player_y, player_health, "Spider-Man")
    draw_health_bar(enemy_x,  enemy_y,  enemy_health,  "Green Goblin")

    screen.blit(ui_font.render(f"Score: {score}", True, (255, 255, 0)), (20, 20))

    if game_over:
        winner  = "THE GREEN GOBLIN" if player_health <= 0 else "SPIDERMAN"
        go_font = pygame.font.SysFont("Berlin Sans FB", 74)
        go_text = go_font.render(f"{winner} Wins!", True, (255, 255, 255))
        screen.blit(go_text, go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    pygame.display.update()
    clock.tick(60)
