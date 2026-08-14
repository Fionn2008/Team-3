import pygame  
import sys  
import random  
import math  
from os.path import join  
  
# Initialize Pygame  
pygame.init()  
  
# Screen setup  
SCREEN_WIDTH = 1280  
SCREEN_HEIGHT = 720  
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  
pygame.display.set_caption("Spiderman - Far From Dublin")
SCREEN_RECT = screen.get_rect()   # cached once — not called every frame
screen_shake = 0
# Player settings  
player1_size = 5  
player2_size = 5  
bomb_size = 10  
  
# Load images  
def scale_to_height(img, target_height):
    """Scale image to target_height while preserving aspect ratio."""
    w, h = img.get_size()
    ratio = target_height / h
    return pygame.transform.scale(img, (int(w * ratio), target_height))

player1_img = pygame.image.load(join("vedha", "images", "spidy.png")).convert_alpha()  
rect = player1_img.get_bounding_rect()  
player1_img = player1_img.subsurface(rect).copy()  
player1_img = scale_to_height(player1_img, 100)
  
player1_shoot_img = pygame.image.load(join("vedha", "images", "spidy_shoot.png")).convert_alpha()  
rect = player1_shoot_img.get_bounding_rect()  
player1_shoot_img = player1_shoot_img.subsurface(rect).copy()  
player1_shoot_img = scale_to_height(player1_shoot_img, 100)
  
# Shooting animation state variables  
is_shooting = False  
shoot_timer = 0  
  
player2_img = pygame.image.load(join("vedha", "images", "docock.png")).convert_alpha()  
rect = player2_img.get_bounding_rect()  
player2_img = player2_img.subsurface(rect).copy()  
player2_img = pygame.transform.scale(player2_img, (100, 100))  
  
bomb_img = pygame.image.load(join("vedha", "images", "bomborange.png")).convert_alpha()  
bomb_img = pygame.transform.scale(bomb_img, (100, 100))  
  
web_img = pygame.image.load(join("vedha", "images", "web.png")).convert_alpha()  
web_img = pygame.transform.scale(web_img, (150, 150))  
  
webs = []  
  
health_img = pygame.image.load(join("vedha", "images", "cfr.png")).convert_alpha()  
health_img = pygame.transform.scale(health_img, (150, 150))  
health_items = []  

HEALTH_SPAWN_EVENT = pygame.USEREVENT + 2  
pygame.time.set_timer(HEALTH_SPAWN_EVENT, 2000)  
  
bg_img = pygame.image.load(join("vedha", "images", "bridge.png")).convert()  
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))  
  
player1_rect = player1_img.get_rect(midbottom=(200, 500))  
player2_rect = player2_img.get_rect(midbottom=(820, 500))  
  
p1_lives = 50  
p2_lives = 50  

# FIX: fonts created ONCE here, not inside the game loop
font         = pygame.font.SysFont("Arial", 40, bold=True)
restart_font = pygame.font.SysFont("Arial", 25, bold=True)

game_over = False  
winner_text = ""  
  
bombs = []  
BOMB_EVENT = pygame.USEREVENT + 1  
pygame.time.set_timer(BOMB_EVENT, 800)  
  
clock = pygame.time.Clock()  
player1_speed = 5  
ai_speed = 3  


# FIX: function defined ONCE outside the loop, not redefined every frame
def draw_character_health(rect, current_lives, max_lives, color):  
    bar_width = 80  
    bar_height = 8  
    bar_x = rect.centerx - (bar_width // 2)  
    bar_y = rect.top - 15  
    ratio = max(0, current_lives) / max_lives  
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))  
    pygame.draw.rect(screen, color,           (bar_x, bar_y, int(bar_width * ratio), bar_height))  
    pygame.draw.rect(screen, (0, 0, 0),       (bar_x, bar_y, bar_width, bar_height), 1)  


def reset_game():  
    global p1_lives, p2_lives, game_over, winner_text, bombs, webs, health_items, is_shooting  
    p1_lives = 50  
    p2_lives = 50 
    game_over = False  
    winner_text = ""  
    bombs.clear()  
    webs.clear()  
    health_items.clear()
    is_shooting = False  
    player1_rect.midbottom = (200, 500)  
    player2_rect.midbottom = (820, 500)  


running = True  
while running:

    # ── FIX: event loop ONLY handles events ──────────────────────
    for event in pygame.event.get():  
        if event.type == pygame.QUIT:  
            running = False  

        if event.type == pygame.KEYDOWN:  
            if game_over and event.key == pygame.K_r:  
                reset_game()  
            elif not game_over and event.key == pygame.K_SPACE:
                dx = player2_rect.centerx - player1_rect.centerx
                dy = player2_rect.centery - player1_rect.centery
                distance = (dx**2 + dy**2) ** 0.5
                if distance != 0:
                    web_speed = 7
                    vx = (dx / distance) * web_speed
                    vy = (dy / distance) * web_speed
                    new_web_rect = web_img.get_rect(center=player1_rect.center)
                    webs.append({'rect': new_web_rect, 'vx': vx, 'vy': vy})
                is_shooting = True
                shoot_timer = 15

        if event.type == BOMB_EVENT and not game_over:
            dx = player1_rect.centerx - player2_rect.centerx
            dy = player1_rect.centery - player2_rect.centery
            distance = (dx**2 + dy**2) ** 0.5
            if distance != 0:
                bomb_speed = 18
                base_angle = math.atan2(dy, dx)
                for angle_offset in (0, math.radians(20), math.radians(-20)):
                    angle = base_angle + angle_offset
                    vel_x = math.cos(angle) * bomb_speed
                    vel_y = math.sin(angle) * bomb_speed
                    new_bomb_rect = bomb_img.get_rect(center=player2_rect.center)
                    bombs.append({'rect': new_bomb_rect, 'vx': vel_x, 'vy': vel_y})

        if event.type == HEALTH_SPAWN_EVENT and not game_over:
            rand_x = random.randint(50, SCREEN_WIDTH - 50)
            rand_y = random.randint(50, SCREEN_HEIGHT - 50)
            item_rect = health_img.get_rect(center=(rand_x, rand_y))
            health_items.append(item_rect)

    # ── FIX: update logic is OUTSIDE event loop — runs exactly once per frame ──
    if not game_over:  
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: player1_rect.x -= player1_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player1_rect.x += player1_speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: player1_rect.y -= player1_speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: player1_rect.y += player1_speed
        player1_rect.clamp_ip(SCREEN_RECT)

        for item in health_items[:]:  
            if item.colliderect(player1_rect):  
                p1_lives += 5  
                health_items.remove(item)  
        if event.type == HEALTH_SPAWN_EVENT and not game_over:
            if len(health_items) < 5:
                rand_x = random.randint(50, SCREEN_WIDTH - 50)
                rand_y = random.randint(50, SCREEN_HEIGHT - 50)
                health_items.append(health_img.get_rect(center=(rand_x, rand_y)))
        doc_dx = player1_rect.centerx - player2_rect.centerx  
        doc_dy = player1_rect.centery - player2_rect.centery  
        doc_dist = (doc_dx**2 + doc_dy**2) ** 0.5  
        if doc_dist > 100:  
            player2_rect.x += int((doc_dx / doc_dist) * ai_speed)  
            player2_rect.y += int((doc_dy / doc_dist) * ai_speed)  
        player2_rect.clamp_ip(SCREEN_RECT)  
        if p2_lives < 20:
    # Phase 2: Enraged Doc Ock moves faster and bomb timer quickens
            current_ai_speed = 5
        else:
            current_ai_speed = 3
        if is_shooting:  
            shoot_timer -= 1  
            if shoot_timer <= 0:  
                is_shooting = False  
            
        for bomb in bombs[:]:  
            bomb['rect'].x += bomb['vx']  
            bomb['rect'].y += bomb['vy']  
            if bomb['rect'].colliderect(player1_rect):  
                p1_lives -= 2 
                screen_shake = 12
                bombs.remove(bomb)  
                if p1_lives <= 0:  
                    game_over = True  
                    winner_text = "Doc Ock Wins!"  
                continue  
            if not SCREEN_RECT.colliderect(bomb['rect']):  
                bombs.remove(bomb)  
  
        for w in webs[:]:  
            w['rect'].x += w['vx']  
            w['rect'].y += w['vy']  
            if w['rect'].colliderect(player2_rect):  
                p2_lives -= 1  
                webs.remove(w)  
                if p2_lives <= 0:  
                    game_over = True  
                    winner_text = "Spiderman Wins!"  
                continue  
            if not SCREEN_RECT.colliderect(w['rect']):  
                webs.remove(w)  

    # ── draw — also outside event loop, runs exactly once per frame ──
    screen.blit(bg_img, (0, 0))  
    render_offset = [0, 0]
    if screen_shake > 0:
     screen_shake -= 1
     render_offset[0] = random.randint(-4, 4)
     render_offset[1] = random.randint(-4, 4)
     screen.blit(bg_img, render_offset)
    if is_shooting:  
        screen.blit(player1_shoot_img, player1_rect)  
    else:  
        screen.blit(player1_img, player1_rect)  
  
    screen.blit(player2_img, player2_rect)  
  
    for bomb in bombs:  
        screen.blit(bomb_img, bomb['rect'])  
  
    for w in webs:  
        screen.blit(web_img, w['rect'])  
  
    for item in health_items:  
        screen.blit(health_img, item)  
  
    if game_over:  
        game_over_text = font.render(f"GAME OVER - {winner_text}", True, (255, 255, 255))  
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  
        restart_text = restart_font.render("Press 'R' to Restart", True, (255, 215, 0))  
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))  
        backdrop_rect = text_rect.union(restart_rect).inflate(40, 40)  
        pygame.draw.rect(screen, (0, 0, 0), backdrop_rect)  
        screen.blit(game_over_text, text_rect)  
        screen.blit(restart_text, restart_rect)
  
    draw_character_health(player1_rect, p1_lives, 50,  (0, 255, 0))  
    draw_character_health(player2_rect, p2_lives, 50, (255, 0, 0))  
  
    pygame.display.flip()  
    clock.tick(60)  
  
pygame.quit()  
sys.exit()
