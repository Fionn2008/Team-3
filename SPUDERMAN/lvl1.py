import pygame
import sys
import random
from os.path import join, dirname, abspath

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder (SPUDERMAN),
# so the game runs correctly regardless of the working directory it's launched from.
BASE_DIR = dirname(abspath(__file__))

# Screen setup — reuse Main.py's window if one already exists, otherwise
# create our own so this file can still be run standalone for testing.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.get_surface()
if screen is None:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spiderman - Far From Dublin")

# Background music — see run_level() for where it's played/stopped.
# Drop your own track in at SPUDERMAN/audio/lvl1_theme.mp3 (see chat for details).
MUSIC_PATH = join(BASE_DIR, "audio", "lvl1_theme.mp3")
try:
    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.set_volume(0.5)
    MUSIC_LOADED = True
except (pygame.error, FileNotFoundError):
    MUSIC_LOADED = False

# Fixed ground level — both characters are locked to this Y position
GROUND_Y = 450

# Player settings (Conor - AI enemy)
player_size = 100
player_speed = 3
player_x = 100
player_y = GROUND_Y

# Player2 settings (Spiderman - controlled by WASD)
player2_size = 80  # a bit smaller than Conor
player2_speed = 5
player2_x = SCREEN_WIDTH - 200
# Bottom-align Spiderman with Conor's feet even though he's a smaller box
PLAYER2_GROUND_Y = GROUND_Y + (player_size - player2_size)
player2_y = PLAYER2_GROUND_Y

# Health settings
CONOR_MAX_HEALTH     = 300
SPIDERMAN_MAX_HEALTH = 120
player_health = CONOR_MAX_HEALTH
player2_health = SPIDERMAN_MAX_HEALTH

CONOR_ATTACK_DAMAGE = 5
SPIDERMAN_ATTACK_DAMAGE = 8  # web shot — a little less than Conor's melee damage
CONOR_ATTACK_RANGE = 120
SPIDERMAN_ATTACK_RANGE = 220  # webs reach very slightly further than before
ATTACK_COOLDOWN = 500
ATTACK_FLASH_MS = 150  # how long the shoot sprite / web visual show after attacking

# Knockback settings
CONOR_KNOCKBACK_DISTANCE = 160
SPIDERMAN_KNOCKBACK_DISTANCE = 80
KNOCKBACK_DURATION = 150

# Chicken fillet roll (health pickup) settings
ROLL_SIZE = 80                  # enlarged from 50
ROLL_HEAL_AMOUNT = 25           # how much health the chicken fillet roll restores
ROLL_SPAWN_INTERVAL = 2000      # ms between chicken fillet roll spawns
roll_active = False
roll_x = 0
roll_y = 0
roll_last_spawn = -ROLL_SPAWN_INTERVAL  # spawn one shortly after game starts

# Glow animation state
roll_glow_tick = 0              # increments each frame to drive the pulse

player_last_attack = 0
player2_last_attack = 0

# Knockback state: (vel_x, vel_y, end_time)
player_knockback = (0, 0, 0)
player2_knockback = (0, 0, 0)

# Game state
game_over = False

# Load images
player_img = pygame.image.load(join(BASE_DIR, "images", "conormcgregor.png")).convert_alpha()
rect = player_img.get_bounding_rect()
player_img = player_img.subsurface(rect).copy()
player_img = pygame.transform.scale(player_img, (100, 100))

# ---------------------------------------------------------------------------
# Conor animation frames
# Each animation has 8 frames; we cycle through them when Conor attacks.
# ---------------------------------------------------------------------------
ANIM_FPS        = 12          # frames per second for the animation
ANIM_FRAME_MS   = 1000 // ANIM_FPS   # ms per frame (~83 ms)

def _load_anim(name, count=8):
    frames = []
    for i in range(1, count + 1):
        img = pygame.image.load(
            join(BASE_DIR, "images", "conor_anims", f"{name}_{i}.png")
        ).convert_alpha()
        r = img.get_bounding_rect()
        img = img.subsurface(r).copy()
        img = pygame.transform.scale(img, (100, 100))
        frames.append(img)
    return frames

conor_anims = {
    "punch": _load_anim("punch"),
    "kick":  _load_anim("kick"),
    "knee":  _load_anim("knee"),
    "idle":  _load_anim("idle", count=4),
    "walk":  _load_anim("walk"),
    "jump":  _load_anim("jump", count=3),
}

# Animation state for Conor
# Each attack triggers the full combo: punch → kick → knee (in order)
CONOR_COMBO = ["punch", "kick", "knee"]

conor_anim_name    = None    # which animation is currently playing (None = idle)
conor_anim_frame   = 0       # current frame index within the active animation
conor_anim_timer   = 0       # ms timestamp of last frame advance
conor_anim_locked  = False   # True while a combo is playing
conor_combo_index  = 0       # which step of CONOR_COMBO we're on

# Idle / walk cycle state (runs whenever no combo is locked)
conor_base_anim   = "idle"   # "idle" or "walk"
conor_base_frame  = 0        # frame index for the base animation
conor_base_timer  = 0        # ms timestamp of last base-frame advance

# ---------------------------------------------------------------------------
# Jump physics
# ---------------------------------------------------------------------------
JUMP_VELOCITY     = -18      # initial upward velocity (pixels per frame)
GRAVITY           = 1.0      # downward acceleration per frame

# Spiderman jump state
spider_vel_y      = 0
spider_is_jumping = False

# Conor jump state
conor_vel_y          = 0
conor_is_jumping     = False
conor_jump_pending   = False   # True when Conor is waiting to mirror Spiderman's jump
conor_jump_delay_end = 0       # ms timestamp when Conor should start his jump

# Conor jump animation state (separate from the combo system)
conor_jump_frame      = 0      # 0=jump_1, 1=jump_2  (airborne frames, looping)
conor_jump_anim_timer = 0
conor_landing         = False  # True while showing jump_3 (landing frame)
conor_landing_timer   = 0      # ms timestamp when landing frame started
LANDING_DISPLAY_MS    = 300    # how long jump_3 shows before returning to idle/walk

player2_img = pygame.image.load(join(BASE_DIR, "images", "spidy.png")).convert_alpha()
rect = player2_img.get_bounding_rect()
player2_img = player2_img.subsurface(rect).copy()
player2_img = pygame.transform.scale(player2_img, (player2_size, player2_size))

# Web-shooting animation — same crop/scale treatment as Conor's frames so
# Spiderman's sprite stays consistent when he swaps to the shoot pose.
player2_shoot_img = pygame.image.load(join(BASE_DIR, "images", "spidy_shoot.png")).convert_alpha()
rect = player2_shoot_img.get_bounding_rect()
player2_shoot_img = player2_shoot_img.subsurface(rect).copy()
player2_shoot_img = pygame.transform.scale(player2_shoot_img, (player2_size, player2_size))

WEB_SIZE = 60
web_img = pygame.image.load(join(BASE_DIR, "images", "web.png")).convert_alpha()
web_img = pygame.transform.scale(web_img, (WEB_SIZE, WEB_SIZE))

bg_img = pygame.image.load(join(BASE_DIR, "images", "cage2.png")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

roll_img = pygame.image.load(join(BASE_DIR, "images", "cfr.png")).convert_alpha()
roll_img = pygame.transform.scale(roll_img, (ROLL_SIZE, ROLL_SIZE))

# Fonts
font          = pygame.font.SysFont(None, 74)
subtitle_font = pygame.font.SysFont(None, 42)
health_font   = pygame.font.SysFont(None, 24)
button_font   = pygame.font.SysFont(None, 48)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def draw_health_bar(x, y, health, max_health):
    """Draws a health bar with numerical health value displayed inside the bar."""
    bar_width = 100
    bar_height = 18
    fill = int(bar_width * (health / max_health))

    pygame.draw.rect(screen, (255, 0, 0),   (x, y - 22, bar_width, bar_height))
    pygame.draw.rect(screen, (0, 255, 0),   (x, y - 22, fill, bar_height))
    pygame.draw.rect(screen, (0, 0, 0),     (x, y - 22, bar_width, bar_height), 2)

    hp_text = health_font.render(str(int(health)), True, (255, 255, 255))
    hp_rect = hp_text.get_rect(center=(x + bar_width // 2, y - 22 + bar_height // 2))
    screen.blit(hp_text, hp_rect)


def get_distance(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def calc_knockback(attacker_x, attacker_y, victim_x, victim_y, distance, kb_dist, kb_duration, now):
    """Returns a knockback state tuple (vel_x, vel_y, end_time) — horizontal only."""
    # Only push left or right depending on which side the victim is on
    dir_x = 1 if victim_x >= attacker_x else -1
    frames = kb_duration / (1000 / 60)
    vel_x = dir_x * kb_dist / frames
    return (vel_x, 0, now + kb_duration)  # vel_y always 0


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


def spawn_roll():
    """Returns a random X position along the ground line for the chicken fillet roll."""
    x = random.randint(80, SCREEN_WIDTH - 80 - ROLL_SIZE)
    y = GROUND_Y + player_size - ROLL_SIZE  # sit on the same ground level as the fighters
    return x, y


def reset_game():
    """Resets all mutable game state back to starting values."""
    global player_x, player_y, player2_x, player2_y
    global player_health, player2_health
    global player_last_attack, player2_last_attack
    global player_knockback, player2_knockback
    global game_over, roll_active, roll_x, roll_y, roll_last_spawn, roll_glow_tick

    player_x, player_y = 100, GROUND_Y
    player2_x, player2_y = SCREEN_WIDTH - 200, PLAYER2_GROUND_Y
    player_health = CONOR_MAX_HEALTH
    player2_health = SPIDERMAN_MAX_HEALTH
    player_last_attack = 0
    player2_last_attack = 0
    player_knockback = (0, 0, 0)
    player2_knockback = (0, 0, 0)
    game_over = False
    roll_active = False
    roll_x, roll_y = 0, 0
    roll_last_spawn = -ROLL_SPAWN_INTERVAL
    roll_glow_tick = 0

    # Reset Conor animation state
    global conor_anim_name, conor_anim_frame, conor_anim_timer, conor_anim_locked
    global conor_combo_index, conor_base_anim, conor_base_frame, conor_base_timer
    conor_anim_name   = None
    conor_anim_frame  = 0
    conor_anim_timer  = 0
    conor_anim_locked = False
    conor_combo_index = 0
    conor_base_anim   = "idle"
    conor_base_frame  = 0
    conor_base_timer  = 0

    # Reset jump state
    global spider_vel_y, spider_is_jumping
    global conor_vel_y, conor_is_jumping, conor_jump_pending, conor_jump_delay_end
    global conor_jump_frame, conor_jump_anim_timer, conor_landing, conor_landing_timer
    spider_vel_y         = 0
    spider_is_jumping    = False
    conor_vel_y          = 0
    conor_is_jumping     = False
    conor_jump_pending   = False
    conor_jump_delay_end = 0
    conor_jump_frame     = 0
    conor_jump_anim_timer = 0
    conor_landing        = False
    conor_landing_timer  = 0


def draw_roll_glow(x, y, tick):
    """Draws a pulsing green glow behind the chicken fillet roll."""
    import math
    # Pulse: radius oscillates between 48 and 64 px
    pulse = int(48 + 16 * math.sin(tick * 0.08))
    glow_surf = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
    # Draw several concentric circles fading outward for a soft glow effect
    for i in range(6, 0, -1):
        radius = int(pulse * i / 6)
        alpha  = int(120 * (i / 6))        # brighter in the centre
        pygame.draw.circle(glow_surf, (80, 255, 80, alpha), (pulse, pulse), radius)
    # cfr.png's actual artwork sits well left of its canvas centre, so shift
    # the glow left to line up with the drawing instead of the empty canvas.
    cx = x + ROLL_SIZE // 2 - 17
    cy = y + ROLL_SIZE // 2
    screen.blit(glow_surf, (cx - pulse, cy - pulse))


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
clock = pygame.time.Clock()


def run_level():
    """
    Runs Level 1 (Conor McGregor) to completion.
    Returns "win" once the player has beaten Conor and pressed SPACE to
    continue. Only exits the process on window close (QUIT event).
    """
    global player_x, player_y, player2_x, player2_y
    global player_health, player2_health
    global player_last_attack, player2_last_attack
    global player_knockback, player2_knockback
    global game_over, roll_active, roll_x, roll_y, roll_last_spawn, roll_glow_tick
    global conor_anim_name, conor_anim_frame, conor_anim_timer, conor_anim_locked
    global conor_combo_index, conor_base_anim, conor_base_frame, conor_base_timer
    global spider_vel_y, spider_is_jumping
    global conor_vel_y, conor_is_jumping, conor_jump_pending, conor_jump_delay_end
    global conor_jump_frame, conor_jump_anim_timer, conor_landing, conor_landing_timer

    reset_game()
    won = False
    if MUSIC_LOADED:
        pygame.mixer.music.play(loops=-1)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        # ---- Event handling ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over and won:
                        if MUSIC_LOADED:
                            pygame.mixer.music.stop()
                        return "win"

                if event.key == pygame.K_UP:
                    # Spiderman jumps on UP ARROW — only when on the ground
                    if not game_over and not spider_is_jumping:
                        spider_vel_y   = JUMP_VELOCITY
                        spider_is_jumping = True
                        # Queue Conor to jump after a short random delay
                        if not conor_is_jumping and not conor_jump_pending:
                            conor_jump_pending   = True
                            conor_jump_delay_end = pygame.time.get_ticks() + random.randint(500, 900)

            # Restart button click (only relevant when Spiderman lost)
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

        # ---- PLAYING ----
        if not game_over:
            keys = pygame.key.get_pressed()

            now = pygame.time.get_ticks()

            # Apply knockback before movement
            if now < player_knockback[2]:
                player_x += player_knockback[0]
                player_y += player_knockback[1]

            if now < player2_knockback[2]:
                player2_x += player2_knockback[0]
                player2_y += player2_knockback[1]

            # Spiderman movement (A/D only) — only when NOT being knocked back
            if now >= player2_knockback[2]:
                if keys[pygame.K_a]:
                    player2_x -= player2_speed
                if keys[pygame.K_d]:
                    player2_x += player2_speed

            # Spiderman jump physics
            if spider_is_jumping:
                spider_vel_y  += GRAVITY
                player2_y     += spider_vel_y
                if player2_y >= PLAYER2_GROUND_Y:
                    player2_y        = PLAYER2_GROUND_Y
                    spider_vel_y     = 0
                    spider_is_jumping = False
            else:
                player2_y = PLAYER2_GROUND_Y

            # Conor AI: chase Spiderman horizontally only — only when NOT being knocked back
            if now >= player_knockback[2]:
                dx = player2_x - player_x
                if dx != 0:
                    player_x += (dx / abs(dx)) * player_speed  # move left or right only

            # Conor jump: trigger after delay, then apply physics
            if conor_jump_pending and now >= conor_jump_delay_end:
                conor_jump_pending    = False
                conor_is_jumping      = True
                conor_vel_y           = JUMP_VELOCITY
                conor_jump_frame      = 0
                conor_jump_anim_timer = now
                conor_landing         = False

            if conor_is_jumping:
                conor_vel_y += GRAVITY
                player_y    += conor_vel_y
                if player_y >= GROUND_Y:
                    player_y         = GROUND_Y
                    conor_vel_y      = 0
                    conor_is_jumping = False
                    # Show landing frame
                    conor_landing       = True
                    conor_landing_timer = now
            else:
                player_y = GROUND_Y

            # Keep players on screen (horizontal only — Y is locked to ground)
            player_x  = max(0, min(player_x,  SCREEN_WIDTH - player_size))
            player2_x = max(0, min(player2_x, SCREEN_WIDTH - player2_size))

            # ---- Chicken fillet roll spawn & collection ----
            if not roll_active and now - roll_last_spawn >= ROLL_SPAWN_INTERVAL:
                roll_x, roll_y = spawn_roll()
                roll_active = True

            if roll_active:
                # Check if Spiderman walks over the chicken fillet roll
                roll_rect      = pygame.Rect(roll_x, roll_y, ROLL_SIZE, ROLL_SIZE)
                spiderman_rect = pygame.Rect(player2_x, player2_y, player2_size, player2_size)
                if spiderman_rect.colliderect(roll_rect):
                    player2_health = min(SPIDERMAN_MAX_HEALTH, player2_health + ROLL_HEAL_AMOUNT)
                    roll_active = False
                    roll_last_spawn = now   # start the cooldown from now

            # Attacks
            distance = get_distance(player_x, player_y, player2_x, player2_y)

            # Conor auto-attacks whenever Spiderman is in range
            if distance < CONOR_ATTACK_RANGE and now - player_last_attack > ATTACK_COOLDOWN:
                player_last_attack = now
                player2_health = max(0, player2_health - CONOR_ATTACK_DAMAGE)
                player2_knockback = calc_knockback(
                    player_x, player_y, player2_x, player2_y, distance,
                    SPIDERMAN_KNOCKBACK_DISTANCE, KNOCKBACK_DURATION, now
                )
                # Start the punch → kick → knee combo from the beginning
                if not conor_anim_locked and not conor_is_jumping and not conor_landing:
                    conor_combo_index = 0
                    conor_anim_name   = CONOR_COMBO[conor_combo_index]
                    conor_anim_frame  = 0
                    conor_anim_timer  = now
                    conor_anim_locked = True

            # Spiderman attacks with SPACE BAR
            if keys[pygame.K_SPACE] and distance < SPIDERMAN_ATTACK_RANGE and now - player2_last_attack > ATTACK_COOLDOWN:
                player2_last_attack = now
                player_health = max(0, player_health - SPIDERMAN_ATTACK_DAMAGE)
                player_knockback = calc_knockback(
                    player2_x, player2_y, player_x, player_y, distance,
                    CONOR_KNOCKBACK_DISTANCE, KNOCKBACK_DURATION, now
                )

            if player_health <= 0 or player2_health <= 0:
                game_over = True
                won = player2_health > 0

        # ---- Draw gameplay ----
        screen.blit(bg_img, (0, 0))

        # Draw chicken fillet roll (glow first, then sprite on top)
        if roll_active:
            roll_glow_tick += 1
            draw_roll_glow(roll_x, roll_y, roll_glow_tick)
            screen.blit(roll_img, (roll_x, roll_y))

        # ---- Advance Conor animation frame ----
        now_draw = pygame.time.get_ticks()

        if conor_is_jumping:
            # Jump has full priority — freeze the combo timer so it doesn't drift,
            # and cycle between jump_1 and jump_2 while airborne
            conor_anim_timer = now_draw   # keep combo timer current so it resumes cleanly
            if now_draw - conor_jump_anim_timer >= ANIM_FRAME_MS:
                conor_jump_frame      = (conor_jump_frame + 1) % 2
                conor_jump_anim_timer = now_draw
        elif conor_landing:
            # Just landed — hold jump_3, freeze everything else
            conor_anim_timer = now_draw
            if now_draw - conor_landing_timer >= LANDING_DISPLAY_MS:
                conor_landing = False
        elif conor_anim_locked and conor_anim_name:
            # Combo attack animation — advance it
            if now_draw - conor_anim_timer >= ANIM_FRAME_MS:
                conor_anim_frame += 1
                conor_anim_timer  = now_draw
                if conor_anim_frame >= len(conor_anims[conor_anim_name]):
                    conor_combo_index += 1
                    if conor_combo_index < len(CONOR_COMBO):
                        conor_anim_name  = CONOR_COMBO[conor_combo_index]
                        conor_anim_frame = 0
                    else:
                        conor_anim_name   = None
                        conor_anim_frame  = 0
                        conor_combo_index = 0
                        conor_anim_locked = False
        else:
            # No combo, not jumping — advance idle or walk cycle
            conor_is_moving = (abs(player2_x - player_x) > player_speed)
            desired_base = "walk" if conor_is_moving else "idle"
            if desired_base != conor_base_anim:
                conor_base_anim  = desired_base
                conor_base_frame = 0
                conor_base_timer = now_draw
            elif now_draw - conor_base_timer >= ANIM_FRAME_MS:
                conor_base_frame = (conor_base_frame + 1) % len(conor_anims[conor_base_anim])
                conor_base_timer = now_draw

        # ---- Pick the right Conor sprite and flip to face Spiderman ----
        if conor_is_jumping:
            conor_frame_img = conor_anims["jump"][conor_jump_frame]      # jump_1 or jump_2
        elif conor_landing:
            conor_frame_img = conor_anims["jump"][2]                     # jump_3 (landing)
        elif conor_anim_locked and conor_anim_name:
            conor_frame_img = conor_anims[conor_anim_name][conor_anim_frame]
        else:
            conor_frame_img = conor_anims[conor_base_anim][conor_base_frame]

        # Flip horizontally when Conor is to the right of Spiderman
        facing_right = player2_x > player_x
        if not facing_right:
            conor_frame_img = pygame.transform.flip(conor_frame_img, True, False)

        screen.blit(conor_frame_img, (player_x, player_y))

        # Spiderman: swap to the shoot pose and draw a web trail to Conor
        # for a short flash after each attack.
        if now_draw - player2_last_attack < ATTACK_FLASH_MS:
            screen.blit(player2_shoot_img, (player2_x, player2_y))
            web_start = (player2_x + player2_size // 2, player2_y + player2_size // 2)
            web_end   = (player_x + player_size // 2, player_y + player_size // 2)
            pygame.draw.line(screen, (255, 255, 255), web_start, web_end, 3)
            screen.blit(web_img, web_img.get_rect(center=web_end))
        else:
            screen.blit(player2_img, (player2_x, player2_y))

        draw_health_bar(player_x,  player_y,  player_health,  CONOR_MAX_HEALTH)
        draw_health_bar(player2_x, player2_y, player2_health, SPIDERMAN_MAX_HEALTH)

        # ---- Game over overlay ----
        if game_over:
            # Semi-transparent dark overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            winner = "SPUDERMAN" if won else "THE NOTORIOUS CONOR MCGREGOR"
            draw_centered_text(f"{winner} Wins!", font, (255, 255, 255), SCREEN_HEIGHT // 2 - 30)

            if won:
                draw_centered_text("Press SPACE to Continue", subtitle_font, (255, 215, 0), SCREEN_HEIGHT // 2 + 30)
            else:
                # Only show restart button if Spiderman lost
                draw_button(
                    "Restart", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 87,
                    220, 55, (220, 60, 60), (255, 100, 100), mouse_pos
                )

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run_level()
    pygame.quit()
    sys.exit()



