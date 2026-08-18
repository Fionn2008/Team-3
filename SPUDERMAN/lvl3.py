import pygame
import sys
import random
from os.path import join, dirname, abspath

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder (SPUDERMAN),
# so the game runs correctly regardless of the working directory it's launched from.
BASE_DIR = dirname(abspath(__file__))
  
# Screen setup  
SCREEN_WIDTH = 1280  
SCREEN_HEIGHT = 720  
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  
pygame.display.set_caption("Spiderman - Far From Dublin")
SCREEN_RECT = screen.get_rect()
screen_shake = 0
last_shot_time = 0

def scale_to_height(img, target_height):
    w, h = img.get_size()
    ratio = target_height / h
    return pygame.transform.scale(img, (int(w * ratio), target_height))

# --- Load Player 1 (Spider-Man) Images ---
player1_img = pygame.image.load(join("vedha", "images", "spidy.png")).convert_alpha()  
rect = player1_img.get_bounding_rect()  
player1_img = player1_img.subsurface(rect).copy()  
player1_img = scale_to_height(player1_img, 100)
  
player1_shoot_img = pygame.image.load(join("vedha", "images", "spidy_shoot.png")).convert_alpha()  
rect = player1_shoot_img.get_bounding_rect()  
player1_shoot_img = player1_shoot_img.subsurface(rect).copy()  
player1_shoot_img = scale_to_height(player1_shoot_img, 100)

is_shooting = False  
shoot_timer = 0  

# --- Load Player 2 (Doc Ock) Images ---
player2_img = pygame.image.load(join("vedha", "images", "docock.png")).convert_alpha()  
rect = player2_img.get_bounding_rect()  
player2_img = player2_img.subsurface(rect).copy()  
player2_img = pygame.transform.scale(player2_img, (100, 100))  

# Doc Ock Shoot Sprite
player2_shoot_img = pygame.image.load(join("vedha", "images", "docockshoot.png")).convert_alpha()
rect = player2_shoot_img.get_bounding_rect()
player2_shoot_img = player2_shoot_img.subsurface(rect).copy()
player2_shoot_img = pygame.transform.scale(player2_shoot_img, (100, 100))

# Enraged Doc Ock Sprites (Normal & Shooting)
red_overlay = pygame.Surface((100, 100), pygame.SRCALPHA)
red_overlay.fill((255, 60, 60, 255))

player2_angry_img = player2_img.copy()
player2_angry_img.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

player2_angry_shoot_img = player2_shoot_img.copy()
player2_angry_shoot_img.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

doc_is_shooting = False
doc_shoot_timer = 0

# --- Webs Setup ---
web_img = pygame.image.load(join("vedha", "images", "web.png")).convert_alpha()  
web_img_small = pygame.transform.scale(web_img, (150, 150))
web_img_large = pygame.transform.scale(web_img, (200, 200))
webs = []  
  
# --- Health Item Setup ---
health_img = pygame.image.load(join("vedha", "images", "cfr.png")).convert_alpha()  
health_img = pygame.transform.scale(health_img, (150, 150))  
health_items = []  
HEALTH_SPAWN_EVENT = pygame.USEREVENT + 1  
pygame.time.set_timer(HEALTH_SPAWN_EVENT, 1000)

# --- Doc Ock Projectiles Setup ---
doc_projectiles = []
doc_last_shot_time = 0
doc_projectile_img = pygame.transform.scale(web_img, (40, 40))

# --- Sound Effects ---
shoot_sound = pygame.mixer.Sound(join("vedha", "sound", "shoot.wav"))
shoot_sound.set_volume(0.6)
super_shoot_sound = pygame.mixer.Sound(join("vedha", "sound", "explode.wav"))
super_shoot_sound.set_volume(0.9)
angry_docock_sound = pygame.mixer.Sound(join("vedha", "sound", "scream.wav"))
angry_docock_sound.set_volume(0.9)

# --- Super Power-Up Setup ---
super_items = []
has_super_power = False
SUPER_SPAWN_EVENT = pygame.USEREVENT + 2
pygame.time.set_timer(SUPER_SPAWN_EVENT, 3000)

particles = []

bg_img = pygame.image.load(join("vedha", "images", "bridge.png")).convert()  
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))  
  
player1_rect = player1_img.get_rect(midbottom=(200, 500))  
player2_rect = player2_img.get_rect(midbottom=(820, 500))  
  
p1_lives = 200  
p2_lives = 200 

# Fonts
title_font   = pygame.font.SysFont("Arial", 26, bold=True)
hud_font     = pygame.font.SysFont("Arial", 20, bold=True)
control_font = pygame.font.SysFont("Arial", 16, italic=True)
font         = pygame.font.SysFont("Arial", 40, bold=True)
restart_font = pygame.font.SysFont("Arial", 25, bold=True)

game_over = False  
winner_text = ""  
clock = pygame.time.Clock()  
player1_speed = 6  
doc_ock_speed = 5
invincible_timer = 0  

def trigger_explosion(x, y):
    """Spawns fiery explosion particles."""
    colors = [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 255, 255)]
    for _ in range(45):
        vx = random.uniform(-8, 8)
        vy = random.uniform(-8, 8)
        radius = random.randint(4, 9)
        color = random.choice(colors)
        life = random.randint(20, 35)
        particles.append([x, y, vx, vy, radius, color, life])

def draw_character_health(rect, current_lives, max_lives, color):  
    bar_width = 80  
    bar_height = 8  
    bar_x = rect.centerx - (bar_width // 2)  
    bar_y = rect.top - 15  
    ratio = max(0, current_lives) / max_lives  
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))  
    pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_width * ratio), bar_height))  
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 1)  

def reset_game():  
    global p1_lives, p2_lives, game_over, winner_text, webs, health_items, super_items
    global is_shooting, doc_is_shooting, invincible_timer, has_super_power, particles, last_shot_time
    global doc_projectiles, doc_last_shot_time
    p1_lives = 200  
    p2_lives = 200
    game_over = False  
    winner_text = ""  
    webs.clear()  
    doc_projectiles.clear()
    health_items.clear()
    super_items.clear()
    particles.clear()
    has_super_power = False
    is_shooting = False  
    doc_is_shooting = False
    invincible_timer = 0
    last_shot_time = 0
    doc_last_shot_time = 0
    player1_rect.midbottom = (200, 500)  
    player2_rect.midbottom = (820, 500)  

running = True  
while running:
    # ── Event Loop ──────────────────────────────────────────
    for event in pygame.event.get():  
        if event.type == pygame.QUIT:  
            running = False  

        if event.type == pygame.KEYDOWN:  
            if game_over and event.key == pygame.K_r:  
                reset_game()  
            elif not game_over and event.key == pygame.K_SPACE:
                current_time = pygame.time.get_ticks()
                shot_cooldown = 150

                if current_time - last_shot_time >= shot_cooldown:
                    last_shot_time = current_time

                    dx = player2_rect.centerx - player1_rect.centerx
                    dy = player2_rect.centery - player1_rect.centery
                    distance = (dx**2 + dy**2) ** 0.5
                    
                    if distance != 0:
                        if has_super_power:
                            if super_shoot_sound:
                                super_shoot_sound.play()
                            web_speed = 12
                            new_web_rect = web_img_large.get_rect(center=player1_rect.center)
                            webs.append({
                                'rect': new_web_rect,
                                'x': float(new_web_rect.centerx),
                                'y': float(new_web_rect.centery),
                                'vx': (dx / distance) * web_speed,
                                'vy': (dy / distance) * web_speed,
                                'is_super': True,
                                'damage': 10
                            })
                            has_super_power = False
                        else:
                            if shoot_sound:
                                shoot_sound.play()
                            web_speed = 9
                            new_web_rect = web_img_small.get_rect(center=player1_rect.center)
                            webs.append({
                                'rect': new_web_rect,
                                'x': float(new_web_rect.centerx),
                                'y': float(new_web_rect.centery),
                                'vx': (dx / distance) * web_speed,
                                'vy': (dy / distance) * web_speed,
                                'is_super': False,
                                'damage': 5
                            })

                    is_shooting = True
                    shoot_timer = 15

        # Spawn Health Item
        if event.type == HEALTH_SPAWN_EVENT and not game_over:
            if len(health_items) < 3:
                rand_x = random.randint(60, SCREEN_WIDTH - 60)
                rand_y = random.randint(60, SCREEN_HEIGHT - 60)
                health_items.append(health_img.get_rect(center=(rand_x, rand_y)))

        # Spawn Super Power Item
        if event.type == SUPER_SPAWN_EVENT and not game_over:
            if len(super_items) < 1 and not has_super_power:
                rand_x = random.randint(80, SCREEN_WIDTH - 80)
                rand_y = random.randint(80, SCREEN_HEIGHT - 80)
                super_items.append(pygame.Rect(rand_x, rand_y, 35, 35))

    # ── Game Update Logic ───────────────────────────────────
    if not game_over:  
        # 1. Spider-Man Movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: player1_rect.x -= player1_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player1_rect.x += player1_speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: player1_rect.y -= player1_speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: player1_rect.y += player1_speed
        player1_rect.clamp_ip(SCREEN_RECT)

        # 2. Health Pickups
        for item in health_items[:]:  
            if item.colliderect(player1_rect):  
                p1_lives = min(50, p1_lives + 10)  
                health_items.remove(item)  

        # 3. Super Power Pickups
        for s_item in super_items[:]:
            if s_item.colliderect(player1_rect):
                has_super_power = True
                super_items.remove(s_item)

        # 4. Doc Ock AI Pursuit
        doc_dx = player1_rect.centerx - player2_rect.centerx  
        doc_dy = player1_rect.centery - player2_rect.centery  
        doc_dist = (doc_dx**2 + doc_dy**2) ** 0.5  

        is_doc_angry = p2_lives <= 50
        current_ai_speed = 10 if is_doc_angry else doc_ock_speed
        
        if is_doc_angry and angry_docock_sound and not pygame.mixer.get_busy():
            angry_docock_sound.play()

        if doc_dist != 0:  
            player2_rect.x += int((doc_dx / doc_dist) * current_ai_speed)  
            player2_rect.y += int((doc_dy / doc_dist) * current_ai_speed)  
        player2_rect.clamp_ip(SCREEN_RECT)  

        # 5. Doc Ock Fast Ranged Attack (Rapid fire homing attacks)
        current_time = pygame.time.get_ticks()
        # Cooldown: 600ms if angry, 900ms regular (fires more than twice as fast)
        doc_cooldown = 200 if is_doc_angry else 500

        if current_time - doc_last_shot_time >= doc_cooldown:
            doc_last_shot_time = current_time
            doc_is_shooting = True
            doc_shoot_timer = 13
            
            proj_rect = doc_projectile_img.get_rect(center=player2_rect.center)
            doc_projectiles.append({
                'rect': proj_rect,
                'x': float(player2_rect.centerx),
                'y': float(player2_rect.centery),
                'speed': 8 if is_doc_angry else 10,   # Faster projectile velocity
                'damage': 5 if is_doc_angry else 2   # Higher damage per hit
            })

        # 6. Doc Ock Melee Attack
        if invincible_timer > 0:
            invincible_timer -= 1
        elif player1_rect.colliderect(player2_rect):
            damage_dealt = 7 if is_doc_angry else 5
            p1_lives -= damage_dealt
            screen_shake = 20 if is_doc_angry else 14
            invincible_timer = 12  
            doc_is_shooting = True
            doc_shoot_timer = 20
            
            if doc_dist != 0:
                knockback_dist = 110 if is_doc_angry else 90
                player1_rect.x += int((doc_dx / doc_dist) * knockback_dist)
                player1_rect.y += int((doc_dy / doc_dist) * knockback_dist)
                player1_rect.clamp_ip(SCREEN_RECT)

            if p1_lives <= 0:  
                game_over = True  
                winner_text = "Doc Ock Wins!"

        # Sprite Timers
        if doc_is_shooting:
            doc_shoot_timer -= 1
            if doc_shoot_timer <= 0:
                doc_is_shooting = False

        if is_shooting:  
            shoot_timer -= 1  
            if shoot_timer <= 0:  
                is_shooting = False  

        # 7. Doc Ock Homing Projectiles (Tracking Spider-Man's exact location)
        for p in doc_projectiles[:]:
            p_dx = player1_rect.centerx - p['x']
            p_dy = player1_rect.centery - p['y']
            dist = (p_dx**2 + p_dy**2) ** 0.5

            if dist > 0:
                p['x'] += (p_dx / dist) * p['speed']
                p['y'] += (p_dy / dist) * p['speed']
                p['rect'].center = (int(p['x']), int(p['y']))

            # Collision with Spider-Man
            if p['rect'].colliderect(player1_rect):
                p1_lives -= p['damage']
                screen_shake = 10
                doc_projectiles.remove(p)
                if p1_lives <= 0:
                    game_over = True
                    winner_text = "Doc Ock Wins!"
                continue

            if not SCREEN_RECT.colliderect(p['rect']):
                doc_projectiles.remove(p)

        # 8. Web Movement & Collision
        for w in webs[:]:  
            w['x'] += w['vx']  
            w['y'] += w['vy']  
            w['rect'].center = (int(w['x']), int(w['y']))
            
            if w['rect'].colliderect(player2_rect):  
                p2_lives -= w['damage']  
                
                if w['is_super']:
                    screen_shake = 22
                    trigger_explosion(player2_rect.centerx, player2_rect.centery)

                webs.remove(w)  
                if p2_lives <= 0:  
                    game_over = True  
                    winner_text = "Spiderman Wins!"  
                continue  
            if not SCREEN_RECT.colliderect(w['rect']):  
                webs.remove(w)  

        # 9. Particle Updates
        for p in particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] = max(0, p[4] - 0.25)
            p[6] -= 1
            if p[6] <= 0:
                particles.remove(p)

    # ── Drawing Section ─────────────────────────────────────
    render_offset = [0, 0]
    if screen_shake > 0:
        screen_shake -= 1
        render_offset[0] = random.randint(-5, 5)
        render_offset[1] = random.randint(-5, 5)

    screen.blit(bg_img, render_offset)  

    # Super Orb
    pulse = abs(pygame.time.get_ticks() % 1000 - 500) // 50
    for s_item in super_items:
        pygame.draw.circle(screen, (255, 215, 0), s_item.center, 18 + pulse)
        pygame.draw.circle(screen, (255, 255, 255), s_item.center, 8)

    # Spider-Man
    if has_super_power:
        pygame.draw.circle(screen, (255, 215, 0), player1_rect.center, 55, 3)

    if invincible_timer % 4 < 2:
        if is_shooting:  
            screen.blit(player1_shoot_img, player1_rect)  
        else:  
            screen.blit(player1_img, player1_rect)  

    # Doc Ock Rendering
    is_doc_angry = p2_lives <= 50
    if is_doc_angry:
        if doc_is_shooting:
            screen.blit(player2_angry_shoot_img, player2_rect)
        else:
            screen.blit(player2_angry_img, player2_rect)
        
        angry_text = control_font.render("⚠ ENRAGED! ⚠", True, (255, 40, 40))
        text_pos = (player2_rect.centerx - (angry_text.get_width() // 2), player2_rect.top - 34)
        screen.blit(angry_text, text_pos)
    else:
        if doc_is_shooting:
            screen.blit(player2_shoot_img, player2_rect)
        else:
            screen.blit(player2_img, player2_rect)

    # Draw Doc Ock Projectiles
    for p in doc_projectiles:
        screen.blit(doc_projectile_img, p['rect'])

    # Draw Spider-Man Webs
    for w in webs:  
        if w['is_super']:
            screen.blit(web_img_large, w['rect'])
        else:
            screen.blit(web_img_small, w['rect'])  

    # Pickups & Particles
    for item in health_items:  
        screen.blit(health_img, item)  

    for p in particles:
        pygame.draw.circle(screen, p[5], (int(p[0]), int(p[1])), int(p[4]))

    # Health Bars
    draw_character_health(player1_rect, p1_lives, 200, (0, 255, 0))  
    draw_character_health(player2_rect, p2_lives, 200, (255, 0, 0))  

    # HUD Text
    title_surface = title_font.render("SPIDER-MAN: FAR FROM DUBLIN", True, (255, 255, 255))
    screen.blit(title_surface, (20, 15))

    spidey_lives_text = hud_font.render(f"Spidey HP: {p1_lives}/200", True, (0, 255, 100))
    screen.blit(spidey_lives_text, (20, 48))

    doc_lives_text = hud_font.render(f"Doc Ock HP: {p2_lives}/200", True, (255, 80, 80))
    screen.blit(doc_lives_text, (SCREEN_WIDTH - doc_lives_text.get_width() - 20, 20))

    if has_super_power:
        super_status = hud_font.render("★ MEGA WEB READY! PRESS SPACE ★", True, (255, 215, 0))
        jam_rect = super_status.get_rect(midtop=(SCREEN_WIDTH // 2, 20))
        pygame.draw.rect(screen, (0, 0, 0), jam_rect.inflate(20, 8))
        screen.blit(super_status, jam_rect)
    
    # Controls Banner
    controls_text = control_font.render("Controls: [WASD / Arrows] Move  |  [SPACE] Shoot Web", True, (220, 220, 220))
    controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
    pygame.draw.rect(screen, (0, 0, 0), controls_rect.inflate(20, 8))
    screen.blit(controls_text, controls_rect)

    # Game Over Overlay
    if game_over:  
        game_over_text = font.render(f"GAME OVER - {winner_text}", True, (255, 255, 255))  
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 15))  
        restart_text = restart_font.render("Press 'R' to Restart", True, (255, 215, 0))  
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))  
        backdrop_rect = text_rect.union(restart_rect).inflate(40, 40)  
        pygame.draw.rect(screen, (0, 0, 0), backdrop_rect)  
        screen.blit(game_over_text, text_rect)  
        screen.blit(restart_text, restart_rect)  

    pygame.display.flip()  
    clock.tick(60)  
  
pygame.quit()  
sys.exit()