import pygame
import sys
from os.path import join, dirname, abspath
from random import randint

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder (SPUDERMAN),
# so the game runs correctly regardless of the working directory it's launched from.
BASE_DIR = dirname(abspath(__file__))

#============================================== Screen setup ======================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
# Reuse Main.py's window if one already exists, otherwise create our own
# so this file can still be run standalone for testing.
screen = pygame.display.get_surface()
if screen is None:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spiderman - Far From Dublin")


# ======================================== Health & Attack settings out loop ==================================

# 100 hearts total; each attack reduces health by 5 hearts
MAX_HEALTH = 100
HEART_DAMAGE = 5

player_health = MAX_HEALTH  # Spider-Man
enemy_health = MAX_HEALTH   # Green Goblin (gg)

ATTACK_DAMAGE = 5
enemy_ATTACK_RANGE = 120                   # enemy's (shorter) attack range
spider_ATTACK_RANGE = 200                  # Spiderman's (longer) attack range
ATTACK_COOLDOWN = 500                      # milliseconds between attacks

player_last_attack = 0
enemy_last_attack = 0


# ============================================= Player identity (Spider-Man) ==========================================================

# Corrected asset swap so spider.png is player and gg.png is enemy
player_img = pygame.image.load(join(BASE_DIR, "images", "spider.png")).convert_alpha()
rect = player_img.get_bounding_rect()
player_img = player_img.subsurface(rect).copy() 
player_img = pygame.transform.scale(player_img, (100, 100))

player_rect = player_img.get_rect(midbottom=(380, 500))

player_size = 100
player_speed = 5
player_x = 400
player_y = 300

# ============================================== Enemy identity (Green Goblin) ==========================================================

enemy_img = pygame.image.load(join(BASE_DIR, "images", "gg.png")).convert_alpha()
rect = enemy_img.get_bounding_rect()
enemy_img = enemy_img.subsurface(rect).copy()
enemy_img = pygame.transform.scale(enemy_img, (100, 100))

enemy_size = 100
enemy_speed = 5
enemy_x = 100
enemy_y = 300

# FONT for game over & UI text
font = pygame.font.SysFont(None, 74)
ui_font = pygame.font.SysFont(None, 24)
subtitle_font = pygame.font.SysFont(None, 42)
button_font = pygame.font.SysFont(None, 48)

# ================================== # HEALTH BAR & ATTACK FUNCTIONS in loop ===============================================

def draw_health_bar(x, y, health, name):
    """Draws a health bar with hearts above a character."""
    bar_width = 100
    bar_height = 12
    fill = int(bar_width * (health / MAX_HEALTH))

    # Health bar background (Red) & Foreground (Green)
    pygame.draw.rect(screen, (255, 0, 0), (x, y - 20, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (x, y - 20, fill, bar_height))
    pygame.draw.rect(screen, (0, 0, 0), (x, y - 20, bar_width, bar_height), 2)

    # Text showing remaining hearts
    text = ui_font.render(f"{name}: {health} Hearts", True, (255, 255, 255))
    screen.blit(text, (x, y - 40))


def get_distance(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


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
    global player_last_attack, enemy_last_attack, game_over

    player_x, player_y = 400, 300
    enemy_x, enemy_y = 100, 300
    player_health = MAX_HEALTH
    enemy_health = MAX_HEALTH
    player_last_attack = 0
    enemy_last_attack = 0
    game_over = False


# =================================== # BACKGROUND IMAGE & ENEMY POSITIONS ===============================================
enemy_positions = []
for i in range(1):
    enemy_positions.append((randint(0, SCREEN_WIDTH), randint(0, SCREEN_HEIGHT)))
bg_img = pygame.image.load(join(BASE_DIR, "images", "SS.FR.png")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# ======================================= # Game loop ======================================================================

clock = pygame.time.Clock()
game_over = False
speed = 5


def run_level():
    """
    Runs Level 2 (Green Goblin) to completion.
    Returns "win" once the player has beaten the Green Goblin and pressed
    SPACE to continue. Only exits the process on window close (QUIT event).
    """
    global player_x, player_y, enemy_x, enemy_y
    global player_health, enemy_health
    global player_last_attack, enemy_last_attack, game_over

    reset_game()
    won = False
    distance = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over and won:
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

        now = pygame.time.get_ticks()

        if not game_over:
            # ====================================== player and enemy movement ============================================
            # ==== Player movement (WASD keys) ===
            keys = pygame.key.get_pressed()

            if keys[pygame.K_a]:
                player_x -= player_speed
            if keys[pygame.K_d]:
                player_x += player_speed
            if keys[pygame.K_w]:
                player_y -= player_speed
            if keys[pygame.K_s]:
                player_y += player_speed

            # ==== Enemy movement (Arrow keys) =======================================================

            if keys[pygame.K_LEFT]:
                enemy_x -= enemy_speed
            if keys[pygame.K_RIGHT]:
                enemy_x += enemy_speed
            if keys[pygame.K_UP]:
                enemy_y -= enemy_speed
            if keys[pygame.K_DOWN]:
                enemy_y += enemy_speed

            # =============================== gg : chase spiderman ==========================================

            dx = player_x - enemy_x
            dy = player_y - enemy_y
            dist_to_target = get_distance(player_x, player_y, enemy_x, enemy_y)

            if dist_to_target > 20:  # keep a small distance so it doesn't jitter
                dir_x = dx / dist_to_target
                dir_y = dy / dist_to_target
                enemy_x += dir_x * (enemy_speed * 0.4)
                enemy_y += dir_y * (enemy_speed * 0.4)

            # ========================= Keep players on screen ==================================

            player_x = max(0, min(player_x, SCREEN_WIDTH - player_size))
            player_y = max(0, min(player_y, SCREEN_HEIGHT - player_size))

            enemy_x = max(0, min(enemy_x, SCREEN_WIDTH - enemy_size))
            enemy_y = max(0, min(enemy_y, SCREEN_HEIGHT - enemy_size))

            # ========================= Restrict players to ground area (no sky / trees) ==================================
            # Ground starts at ~y=320 based on the background image; block both players above this line
            GROUND_TOP = 320
            player_y = max(GROUND_TOP, player_y)
            enemy_y  = max(GROUND_TOP, enemy_y)

            # ========================= Restrict players to ground area (no sky / trees) ==================================
            # The ground in the background starts at roughly y=320; keep both characters on the grass only
            GROUND_TOP = 320
            player_y = max(GROUND_TOP, player_y)
            enemy_y  = max(GROUND_TOP, enemy_y)

             # ========================= Attacking ===============================================

            distance = get_distance(player_x, player_y, enemy_x, enemy_y)

            # Green Goblin (gg) auto-attacks Spiderman whenever in range (-5 hearts)
            if distance < enemy_ATTACK_RANGE and now - enemy_last_attack > ATTACK_COOLDOWN:
                enemy_last_attack = now
                player_health = max(0, player_health - HEART_DAMAGE)

            # Spiderman attacks with LEFT CLICK (mouse button 0) (-5 hearts)
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0] and now - player_last_attack > ATTACK_COOLDOWN:
                player_last_attack = now
                if distance < spider_ATTACK_RANGE:
                    enemy_health = max(0, enemy_health - HEART_DAMAGE)

            if player_health <= 0 or enemy_health <= 0:
                game_over = True
                won = player_health > 0

        # ============================= Draw everything =====================================================

        screen.blit(bg_img, (0, 0))
        screen.blit(player_img, (player_x, player_y))
        screen.blit(enemy_img, (enemy_x, enemy_y))

        # Draw web beam when Spiderman attacks with Left Click
        if pygame.mouse.get_pressed()[0] and now - player_last_attack < 150 and distance < spider_ATTACK_RANGE:
            pygame.draw.line(screen, (255, 255, 255), (player_x + 50, player_y + 50), (enemy_x + 50, enemy_y + 50), 3)

        # ======================================== Health bar ===================================================

        draw_health_bar(player_x, player_y, player_health, "Spider-Man")
        draw_health_bar(enemy_x, enemy_y, enemy_health, "Green Goblin")

        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            winner = "SPIDERMAN" if won else "THE GREEN GOBLIN"
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