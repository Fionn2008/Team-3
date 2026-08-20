import pygame
import sys
import random
from os.path import join, dirname, abspath
from random import randint

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder (SPUDERMAN),
# so the game runs correctly regardless of the working directory it's launched from.
BASE_DIR = dirname(abspath(__file__))

# ============================================== Screen setup ======================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
# Reuse Main.py's window if one already exists, otherwise create our own
# so this file can still be run standalone for testing.
screen = pygame.display.get_surface()
if screen is None:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spiderman - Far From Dublin")
SCREEN_RECT = screen.get_rect()

# Background music — see run_level() for where it's played/stopped.
MUSIC_PATH = join(BASE_DIR, "audio", "lvl2_theme.mp3")
try:
    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.set_volume(0.5)
    MUSIC_LOADED = True
except (pygame.error, FileNotFoundError):
    MUSIC_LOADED = False

# ======================================== Health & Attack settings ================================================
MAX_HEALTH = 250
HEART_DAMAGE = 5

player_health = MAX_HEALTH  # Spider-Man
enemy_health = MAX_HEALTH   # Green Goblin (gg)

enemy_ATTACK_RANGE = 120    # Enemy melee range
ATTACK_COOLDOWN = 400       # Milliseconds between attacks

player_last_attack = 0
enemy_last_attack = 0
screen_shake = 0

def scale_to_height(img, target_height):
    w, h = img.get_size()
    ratio = target_height / h
    return pygame.transform.scale(img, (int(w * ratio), target_height))

# ============================================= Player Identity (Spider-Man) =======================================
player_img = pygame.image.load(join(BASE_DIR, "images", "spidy.png")).convert_alpha()
rect = player_img.get_bounding_rect()
player_img = player_img.subsurface(rect).copy()
player_img = scale_to_height(player_img, 100)

player_shoot_img = pygame.image.load(join(BASE_DIR, "images", "spidy_shoot.png")).convert_alpha()
rect = player_shoot_img.get_bounding_rect()  
player_shoot_img = player_shoot_img.subsurface(rect).copy()  
player_shoot_img = scale_to_height(player_shoot_img, 100)

player_w, player_h = player_img.get_size()
player_speed = 5
player_x = 400
player_y = 400

# ============================================== Enemy Identity (Green Goblin) =====================================
enemy_img = pygame.image.load(join(BASE_DIR, "images", "gg.png")).convert_alpha()
rect = enemy_img.get_bounding_rect()
enemy_img = enemy_img.subsurface(rect).copy()
enemy_img = pygame.transform.scale(enemy_img, (100, 100))

enemy_w, enemy_h = enemy_img.get_size()
enemy_speed = 5
enemy_x = 100
enemy_y = 400

# ============================================== Bomb Setup ========================================================
try:
    bomb_img = pygame.image.load(join(BASE_DIR, "images", "bomborange.png")).convert_alpha()
    bomb_img = pygame.transform.scale(bomb_img, (100, 100))
except (pygame.error, FileNotFoundError):
    bomb_img = pygame.Surface((35, 35), pygame.SRCALPHA)
    pygame.draw.circle(bomb_img, (255, 140, 0), (17, 17), 16)

bombs = []
BOMB_EVENT = pygame.USEREVENT + 3
pygame.time.set_timer(BOMB_EVENT, 1200)  # Goblin throws a bomb every 1.2 seconds

# ============================================== Collectibles Setup ================================================
# 1. Health Item (e.g., food/medkit)
try:
    health_img = pygame.image.load(join(BASE_DIR, "images", "cfr.png")).convert_alpha()
    health_img = pygame.transform.scale(health_img, (150, 150))
except (pygame.error, FileNotFoundError):
    health_img = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.circle(health_img, (0, 255, 100), (20, 20), 18)

health_items = []
HEALTH_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(HEALTH_SPAWN_EVENT, 2000)  # Spawn every 4 seconds

# 2. Super Power Orb Collectible
super_items = []
has_super_power = False
SUPER_SPAWN_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(SUPER_SPAWN_EVENT, 4000)   # Spawn every 8 seconds

# Explosion particles: [x, y, vx, vy, radius, color, life]
particles = []

def trigger_explosion(x, y):
    colors = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 255, 255)]
    for _ in range(40):
        vx = random.uniform(-6, 6)
        vy = random.uniform(-6, 6)
        radius = random.randint(4, 8)
        color = random.choice(colors)
        life = random.randint(20, 35)
        particles.append([x, y, vx, vy, radius, color, life])

# ============================================== UI & Fonts ========================================================
font = pygame.font.SysFont("Berlin Sans FB", 74)
ui_font = pygame.font.SysFont("berlinsansfb", 22, bold=True)
hud_font = pygame.font.SysFont("Arial", 20, bold=True)
subtitle_font = pygame.font.SysFont(None, 42)
button_font = pygame.font.SysFont(None, 48)


def draw_centered_text(text, fnt, color, y):
    """Renders text centred horizontally at the given y position."""
    surface = fnt.render(text, True, color)
    r = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(surface, r)


def draw_button(text, cx, cy, w, h, color, hover_color, mouse_pos):
    """Draws a rectangular button and returns its Rect."""
    btn_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    col = hover_color if btn_rect.collidepoint(mouse_pos) else color
    pygame.draw.rect(screen, col, btn_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=10)
    label = button_font.render(text, True, (0, 0, 0))
    label_rect = label.get_rect(center=(cx, cy))
    screen.blit(label, label_rect)
    return btn_rect


def reset_game():
    """Resets all mutable game state back to starting values."""
    global player_x, player_y, enemy_x, enemy_y
    global player_health, enemy_health
    global player_last_attack, enemy_last_attack
    global game_over, screen_shake, has_super_power

    player_x, player_y = 400, 400
    enemy_x, enemy_y = 100, 400
    player_health = MAX_HEALTH
    enemy_health = MAX_HEALTH
    player_last_attack = 0
    enemy_last_attack = 0
    game_over = False
    screen_shake = 0
    has_super_power = False
    bombs.clear()
    health_items.clear()
    super_items.clear()
    particles.clear()


def draw_health_bar(x, y, health, name):
    bar_width = 100
    bar_height = 12
    fill = int(bar_width * (max(0, health) / MAX_HEALTH))

    pygame.draw.rect(screen, (255, 0, 0), (x, y - 20, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (x, y - 20, fill, bar_height))
    pygame.draw.rect(screen, (0, 0, 0), (x, y - 20, bar_width, bar_height), 2)
    
    text = ui_font.render(f"{name}: {health}", True, (255, 255, 255))
    screen.blit(text, (x, y - 40))

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

# ============================================== Background ========================================================
bg_img = pygame.image.load(join(BASE_DIR, "images", "SS.FR.png")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# ============================================== Game Loop =========================================================
clock = pygame.time.Clock()
game_over = False
GROUND_TOP = 320


def run_level():
    """
    Runs Level 2 (Green Goblin) to completion.
    Returns "win" once the player has beaten the Green Goblin and pressed
    SPACE to continue. Only exits the process on window close (QUIT event).
    """
    global player_x, player_y, enemy_x, enemy_y
    global player_health, enemy_health
    global player_last_attack, enemy_last_attack
    global screen_shake, has_super_power, game_over

    reset_game()
    won = False
    if MUSIC_LOADED:
        pygame.mixer.music.play(loops=-1)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        now = pygame.time.get_ticks()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over and won:
                    if MUSIC_LOADED:
                        pygame.mixer.music.stop()
                    return "win"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over and not won:
                    restart_rect = pygame.Rect(
                        SCREEN_WIDTH // 2 - 110,
                        SCREEN_HEIGHT // 2 + 60,
                        220, 55
                    )
                    if restart_rect.collidepoint(mouse_pos):
                        reset_game()
                        won = False

            # Spawn Bombs fired from Green Goblin toward Spider-Man
            if event.type == BOMB_EVENT and not game_over:
                target_dx = (player_x + player_w // 2) - (enemy_x + enemy_w // 2)
                target_dy = (player_y + player_h // 2) - (enemy_y + enemy_h // 2)
                distance = (target_dx**2 + target_dy**2) ** 0.5

                if distance != 0:
                    bomb_speed = 9
                    vel_x = (target_dx / distance) * bomb_speed
                    vel_y = (target_dy / distance) * bomb_speed
                    new_bomb_rect = bomb_img.get_rect(center=(enemy_x + enemy_w // 2, enemy_y + enemy_h // 2))
                    bombs.append({'rect': new_bomb_rect, 'vx': vel_x, 'vy': vel_y})

            # Spawn Health Item
            if event.type == HEALTH_SPAWN_EVENT and not game_over:
                if len(health_items) < 6:
                    rand_x = randint(50, SCREEN_WIDTH - 80)
                    rand_y = randint(GROUND_TOP + 20, SCREEN_HEIGHT - 80)
                    health_items.append(pygame.Rect(rand_x, rand_y, 45, 45))

            # Spawn Super Power Orb
            if event.type == SUPER_SPAWN_EVENT and not game_over:
                if len(super_items) < 1 and not has_super_power:
                    rand_x = randint(50, SCREEN_WIDTH - 80)
                    rand_y = randint(GROUND_TOP + 20, SCREEN_HEIGHT - 80)
                    super_items.append(pygame.Rect(rand_x, rand_y, 35, 35))

        if not game_over:
            # ==================== Player movement (WASD) ====================
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  player_x -= player_speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: player_x += player_speed
            if keys[pygame.K_w] or keys[pygame.K_UP]:    player_y -= player_speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  player_y += player_speed

            # ==================== Green Goblin: Chase Spider-Man ============
            dx = (player_x + player_w // 2) - (enemy_x + enemy_w // 2)
            dy = (player_y + player_h // 2) - (enemy_y + enemy_h // 2)
            dist_to_target = (dx**2 + dy**2) ** 0.5

            if dist_to_target > 25:
                dir_x = dx / dist_to_target
                dir_y = dy / dist_to_target
                enemy_x += dir_x * (enemy_speed * 0.6)
                enemy_y += dir_y * (enemy_speed * 0.6)

            # ==================== Bounds & Ground Restrictions ==============
            player_x = max(0, min(player_x, SCREEN_WIDTH - player_w))
            player_y = max(GROUND_TOP, min(player_y, SCREEN_HEIGHT - player_h))

            enemy_x = max(0, min(enemy_x, SCREEN_WIDTH - enemy_w))
            enemy_y = max(GROUND_TOP, min(enemy_y, SCREEN_HEIGHT - enemy_h))

            player_rect = pygame.Rect(player_x, player_y, player_w, player_h)
            enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_w, enemy_h)

            # ==================== Collectibles Check ========================
            # 1. Health Collectibles (+15 HP)
            for item in health_items[:]:
                if player_rect.colliderect(item):
                    player_health = min(MAX_HEALTH, player_health + 15)
                    health_items.remove(item)

            # 2. Super Power Collectibles (Unlocks Super Blast)
            for s_item in super_items[:]:
                if player_rect.colliderect(s_item):
                    has_super_power = True
                    super_items.remove(s_item)

            # ==================== Bomb Movement & Collisions ================
            for bomb in bombs[:]:
                bomb['rect'].x += bomb['vx']
                bomb['rect'].y += bomb['vy']

                # Hit Spider-Man -> Explosions trigger ONLY on hit
                if bomb['rect'].colliderect(player_rect):
                    player_health = max(0, player_health - 10)
                    screen_shake = 10
                    trigger_explosion(bomb['rect'].centerx, bomb['rect'].centery)
                    bombs.remove(bomb)
                    continue

                # Off-screen bombs vanish quietly without exploding
                if not SCREEN_RECT.colliderect(bomb['rect']):
                    bombs.remove(bomb)

            # ==================== Attacking System ==========================
            # Enemy Melee Auto-Attack
            if dist_to_target < enemy_ATTACK_RANGE and now - enemy_last_attack > ATTACK_COOLDOWN:
                enemy_last_attack = now
                player_health = max(0, player_health - HEART_DAMAGE)

            # Spider-Man Spacebar Attack (Anywhere on Screen)
            if keys[pygame.K_SPACE] and now - player_last_attack > ATTACK_COOLDOWN:
                player_last_attack = now
                if has_super_power:
                    # Mega Blast: 25 damage + explosion effect
                    enemy_health = max(0, enemy_health - 25)
                    trigger_explosion(enemy_rect.centerx, enemy_rect.centery)
                    screen_shake = 16
                    has_super_power = False
                else:
                    # Standard Attack: 5 damage
                    enemy_health = max(0, enemy_health - HEART_DAMAGE)

            # ==================== Update Particles ==========================
            for p in particles[:]:
                p[0] += p[2]
                p[1] += p[3]
                p[4] = max(0, p[4] - 0.2)
                p[6] -= 1
                if p[6] <= 0:
                    particles.remove(p)

            if player_health <= 0 or enemy_health <= 0:
                game_over = True
                won = player_health > 0

        # ============================= Draw Everything =====================================================
        render_offset = [0, 0]
        if screen_shake > 0:
            screen_shake -= 1
            render_offset[0] = random.randint(-4, 4)
            render_offset[1] = random.randint(-4, 4)

        screen.blit(bg_img, render_offset)

        # Draw Health Items
        for item in health_items:
            screen.blit(health_img, item.topleft)

        # Draw Super Power Orbs (Pulsing Golden Orb)
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) // 60
        for s_item in super_items:
            pygame.draw.circle(screen, (255, 215, 0), s_item.center, 18 + pulse)
            pygame.draw.circle(screen, (255, 255, 255), s_item.center, 8)

        # Draw Bombs
        for bomb in bombs:
            screen.blit(bomb_img, bomb['rect'])

        # Draw Player Aura if Super Powered (Accurately Centered on Spider-Man)
        if has_super_power and not game_over:
            player_rect = pygame.Rect(player_x, player_y, player_w, player_h)
            pygame.draw.circle(screen, (255, 215, 0), player_rect.center, (max(player_w, player_h) // 2) + 12, 3)

        # Draw Characters (Swapping to shooting pose during attack)
        if now - player_last_attack < 150:
            screen.blit(player_shoot_img, (player_x, player_y))
        else:
            screen.blit(player_img, (player_x, player_y))

        screen.blit(enemy_img, (enemy_x, enemy_y))

        # Draw Web Beam on Spacebar Attack (Reaches across the whole screen to Goblin)
        if now - player_last_attack < 150:
            beam_color = (255, 215, 0) if has_super_power else (255, 255, 255)
            beam_width = 8 if has_super_power else 3
            beam_start = (player_x + player_w // 2, player_y + player_h // 2)
            beam_end = (enemy_x + enemy_w // 2, enemy_y + enemy_h // 2)
            pygame.draw.line(screen, beam_color, beam_start, beam_end, beam_width)

        # Draw Explosion Particles
        for p in particles:
            pygame.draw.circle(screen, p[5], (int(p[0]), int(p[1])), int(p[4]))

        # Draw Health Bars
        draw_health_bar(player_x, player_y, player_health, "Spider-Man")
        draw_health_bar(enemy_x, enemy_y, enemy_health, "Green Goblin")

        # HUD Status for Super Power
        if has_super_power and not game_over:
            power_text = hud_font.render("★ MEGA WEB READY! PRESS SPACE TO FIRE ★", True, (255, 215, 0))
            power_rect = power_text.get_rect(midtop=(SCREEN_WIDTH // 2, 20))
            pygame.draw.rect(screen, (0, 0, 0), power_rect.inflate(20, 8))
            screen.blit(power_text, power_rect)

        # Game Over Screen
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            winner = "SPIDER-MAN" if won else "THE GREEN GOBLIN"
            draw_centered_text(f"{winner} Wins!", font, (255, 255, 255), SCREEN_HEIGHT // 2 - 30)

            if won:
                draw_centered_text("Press SPACE to Continue", subtitle_font, (255, 215, 0), SCREEN_HEIGHT // 2 + 30)
            else:
                draw_button(
                    "Restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 87,
                    220, 55, (220, 60, 60), (255, 100, 100), mouse_pos
                )

        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    run_level()
    pygame.quit()
    sys.exit()
    clock.tick(60)