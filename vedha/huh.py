import pygame
import sys
from os.path import join

# Initialize Pygame
pygame.init()

# Screen setup
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spiderman - Far From Dublin")

# Player settings
player1_size = 5
player2_size = 5
bomb_size = 10

# Load images
player1_img = pygame.image.load(join("vedha", "images", "spidy.png")).convert_alpha()
rect = player1_img.get_bounding_rect()
player1_img = player1_img.subsurface(rect).copy()
player1_img = pygame.transform.scale(player1_img, (100, 100))

# --- LOAD SPIDER-MAN SHOOTING IMAGE ---
player1_shoot_img = pygame.image.load(join("vedha", "images", "spidy_shoot.png")).convert_alpha()
rect = player1_shoot_img.get_bounding_rect()
player1_shoot_img = player1_shoot_img.subsurface(rect).copy()
player1_shoot_img = pygame.transform.scale(player1_shoot_img, (100, 100))

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
web_img = pygame.transform.scale(web_img, (40, 20))  # Resized web dimensions

webs = []

bg_img = pygame.image.load(join("vedha", "images", "bridge.png")).convert()
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

player1_rect = player1_img.get_rect(midbottom=(200, 500))
player2_rect = player2_img.get_rect(midbottom=(820, 500))

p1_lives = 3
p2_lives = 5
font = pygame.font.SysFont("Arial", 40, bold=True)
game_over = False
winner_text = ""

# Bomb list & Timer
bombs = []
BOMB_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(BOMB_EVENT, 1500)

# Game loop
clock = pygame.time.Clock()
player1_speed = 5
ai_speed = 3

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_SPACE:
                # Calculate direction vector toward Doc Ock's current position
                dx = player2_rect.centerx - player1_rect.centerx
                dy = player2_rect.centery - player1_rect.centery
                distance = (dx**2 + dy**2) ** 0.5

                if distance != 0:
                    web_speed = 10
                    vx = (dx / distance) * web_speed
                    vy = (dy / distance) * web_speed

                    new_web_rect = web_img.get_rect(center=player1_rect.center)
                    webs.append({'rect': new_web_rect, 'vx': vx, 'vy': vy})

                is_shooting = True
                shoot_timer = 15

        # Fire a bomb toward Spidey
        if event.type == BOMB_EVENT and not game_over:
            dx = player1_rect.centerx - player2_rect.centerx
            dy = player1_rect.centery - player2_rect.centery
            distance = (dx**2 + dy**2) ** 0.5
            
            if distance != 0:
                bomb_speed = 7
                vel_x = (dx / distance) * bomb_speed
                vel_y = (dy / distance) * bomb_speed
                
                new_bomb_rect = bomb_img.get_rect(center=player2_rect.center)
                bombs.append({
                    'rect': new_bomb_rect,
                    'vx': vel_x,
                    'vy': vel_y
                })

    if not game_over:
        # 1. SPIDER-MAN CONTROLS
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player1_rect.x -= player1_speed
        if keys[pygame.K_RIGHT]:
            player1_rect.x += player1_speed
        if keys[pygame.K_UP]:
            player1_rect.y -= player1_speed
        if keys[pygame.K_DOWN]:
            player1_rect.y += player1_speed

        # Count down shoot animation timer
        if is_shooting:
            shoot_timer -= 1
            if shoot_timer <= 0:
                is_shooting = False

        # Keep Spider-Man on screen
        player1_rect.clamp_ip(screen.get_rect())

        # 2. UPDATE BOMBS
        for bomb in bombs[:]:
            bomb['rect'].x += bomb['vx']
            bomb['rect'].y += bomb['vy']

            # Check collision with Spider-Man
            if bomb['rect'].colliderect(player1_rect):
                p1_lives -= 1
                bombs.remove(bomb)
                if p1_lives <= 0:
                    game_over = True
                    winner_text = "Doc Ock Wins!"
                continue

            # Remove off-screen bombs
            if not screen.get_rect().colliderect(bomb['rect']):
                bombs.remove(bomb)

        # 3. UPDATE WEBS
        for w in webs[:]:
            w['rect'].x += w['vx']
            w['rect'].y += w['vy']

            # Check if web hits Doc Ock
            if w['rect'].colliderect(player2_rect):
                print("Doc Ock hit by web!")
                p2_lives -= 1
                webs.remove(w)

                if p2_lives <= 0:
                    game_over = True
                    winner_text = "Spiderman Wins!"
                continue

            # Remove webs that go off screen (Fixed typo here)
            if not screen.get_rect().colliderect(w['rect']):
                webs.remove(w)

    # 4. DRAW EVERYTHING
    screen.blit(bg_img, (0, 0))

    # Switch image if Spider-Man is currently shooting
    if is_shooting:
        screen.blit(player1_shoot_img, player1_rect)
    else:
        screen.blit(player1_img, player1_rect)

    screen.blit(player2_img, player2_rect)

    for bomb in bombs:
        screen.blit(bomb_img, bomb['rect'])

    # DRAW WEBS ON SCREEN
    for w in webs:
        screen.blit(web_img, w['rect'])

    # --- DRAW LIVES HUD ---
    lives_text = font.render(f"Lives: {'♥ ' * p1_lives}", True, (255, 0, 0))
    screen.blit(lives_text, (20, 20))

    # --- DRAW GAME OVER TEXT ---
    if game_over:
        game_over_text = font.render(f"GAME OVER - {winner_text}", True, (255, 255, 255))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        pygame.draw.rect(screen, (0, 0, 0), text_rect.inflate(20, 20))
        screen.blit(game_over_text, text_rect)

    # Function to draw a health bar above player heads
    def draw_character_health(rect, current_lives, max_lives, color):
        bar_width = 80
        bar_height = 8
        bar_x = rect.centerx - (bar_width // 2)
        bar_y = rect.top - 15
        
        ratio = max(0, current_lives) / max_lives
        
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_width * ratio), bar_height))
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 1)

    # Draw Spider-Man's health bar
    draw_character_health(player1_rect, p1_lives, 3, (0, 255, 0))

    # Draw Doc Ock's health bar
    draw_character_health(player2_rect, p2_lives, 5, (255, 0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()