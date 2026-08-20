import pygame
import sys
from os.path import join, dirname, abspath
import credits
import cutscene

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder
BASE_DIR = dirname(abspath(__file__))

# Screen setup
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spuderman - Far From Dublin")

# Import levels after the display exists so each one reuses this window
import lvl1
import lvl2
import lvl3

# ── Color Palette (Red, Blue, Black & Accents) ─────────────────
COLOR_BLACK       = (3, 4, 10)
COLOR_DARK_NAVY   = (6, 8, 20)
COLOR_RED_PRIMARY = (204, 17, 17)
COLOR_RED_HOVER   = (255, 34, 34)
COLOR_BLUE_ACCENT = (26, 42, 138)
COLOR_CYAN_GLOW   = (60, 120, 220)
COLOR_WHITE       = (240, 232, 232)
COLOR_MUTED_BLUE  = (160, 180, 220)

# Fonts
font          = pygame.font.SysFont(None, 74)
subtitle_font = pygame.font.SysFont(None, 42)
info_font     = pygame.font.SysFont(None, 36)
button_font   = pygame.font.SysFont(None, 48)

# Background
start_bg_img = pygame.image.load(join(BASE_DIR, "images", "start screen.png")).convert()
start_bg_img = pygame.transform.scale(start_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Cutscene videos
INTRO_VIDEO = join(BASE_DIR, "Cutstart.mp4")  # plays once START is pressed
END_VIDEO   = join(BASE_DIR, "Cutend.mp4")    # plays after Level 3 is beaten

# Game states
START    = "start"
SETTINGS = "settings"
VICTORY  = "victory"
game_state = START

SETTINGS_BACK_BTN_Y = 648


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def draw_centered_text(text, fnt, color, y):
    surface = fnt.render(text, True, color)
    r = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(surface, r)


def draw_fancy_button(text, cx, cy, w, h, mouse_pos):
    btn_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    hovered  = btn_rect.collidepoint(mouse_pos)

    # Drop Shadow
    shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                     shadow_surf.get_rect(), border_radius=14)
    screen.blit(shadow_surf, btn_rect.move(4, 4).topleft)

    # Base Panel: Deep Blue-Black
    panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_color = (18, 22, 45, 230) if hovered else (8, 10, 24, 190)
    pygame.draw.rect(panel_surf, bg_color, panel_surf.get_rect(), border_radius=14)
    screen.blit(panel_surf, btn_rect.topleft)

    # Border: Red on hover, Blue accent at rest
    border_col = COLOR_RED_HOVER if hovered else COLOR_BLUE_ACCENT
    pygame.draw.rect(screen, border_col, btn_rect, width=3, border_radius=14)

    # Top specular highlight
    hi = pygame.Surface((w - 20, 3), pygame.SRCALPHA)
    hi.fill((255, 255, 255, 60 if hovered else 25))
    screen.blit(hi, (btn_rect.x + 10, btn_rect.y + 6))

    # Text & Drop Shadow
    label_shadow = button_font.render(text, True, COLOR_BLACK)
    text_col     = COLOR_RED_HOVER if hovered else COLOR_WHITE
    label        = button_font.render(text, True, text_col)

    lr = label.get_rect(center=(cx, cy))
    screen.blit(label_shadow, lr.move(2, 2))
    screen.blit(label, lr)

    return btn_rect


def draw_start_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))

    # Deep dark-blue/black gradient overlay for contrast
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for row in range(SCREEN_HEIGHT):
        alpha = int(210 * max(0, (row - SCREEN_HEIGHT // 4)) / (SCREEN_HEIGHT * 3 // 4))
        pygame.draw.line(overlay, (4, 6, 14, alpha), (0, row), (SCREEN_WIDTH, row))
    screen.blit(overlay, (0, 0))

    # Main Title (Red with stacked deep red drop-shadows)
    for offset in range(5, 0, -1):
        shadow = font.render("Spuderman", True, (110, 0, 0))
        r = shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset, 140 + offset))
        screen.blit(shadow, r)

    title_surf = font.render("Spuderman", True, COLOR_RED_HOVER)
    screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 140)))

    # Subtitle (Blue accent with subtle glow)
    sub_shadow = subtitle_font.render("Far From Dublin", True, (10, 15, 45))
    screen.blit(sub_shadow, sub_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 207)))
    sub_surf = subtitle_font.render("Far From Dublin", True, COLOR_CYAN_GLOW)
    screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 205)))

    # Red & Blue divider lines
    mid_x = SCREEN_WIDTH // 2
    pygame.draw.line(screen, COLOR_RED_PRIMARY, (mid_x - 220, 230), (mid_x + 220, 230), 2)
    pygame.draw.line(screen, COLOR_BLUE_ACCENT, (mid_x - 180, 234), (mid_x + 180, 234), 1)

    # Menu Buttons
    start_rect    = draw_fancy_button("▶  START",    mid_x, 360, 280, 60, mouse_pos)
    settings_rect = draw_fancy_button("⚙  SETTINGS", mid_x, 445, 280, 60, mouse_pos)
    quit_rect     = draw_fancy_button("✕  QUIT",     mid_x, 530, 280, 60, mouse_pos)
    return start_rect, settings_rect, quit_rect


def draw_settings_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((2, 3, 8, 200))
    screen.blit(overlay, (0, 0))

    card_w, card_h = 700, 500
    card_x = SCREEN_WIDTH  // 2 - card_w // 2
    card_y = 90

    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (8, 12, 26, 235),
                     card_surf.get_rect(), border_radius=18)
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, COLOR_BLUE_ACCENT,
                     (card_x, card_y, card_w, card_h), width=2, border_radius=18)

    draw_centered_text("Settings", font, COLOR_RED_HOVER, card_y + 52)
    pygame.draw.line(screen, COLOR_RED_PRIMARY,
                     (card_x + 40, card_y + 98),
                     (card_x + card_w - 40, card_y + 98), 2)
    draw_centered_text("Controls", subtitle_font, COLOR_MUTED_BLUE, card_y + 128)

    controls = [
        ("A / D",         "Move Spiderman left and right"),
        ("SPACE",         "Jump / Shoot Webs (per level)"),
        ("Left Click",    "Attack (must be in range)"),
        ("Chicken Roll",  "Walk over it to restore HP"),
        ("Enemy AI",      "Chases and auto-attacks you"),
        ("Win Condition", "Beat all 3 levels to finish"),
    ]
    mid_x = SCREEN_WIDTH // 2
    for i, (key, val) in enumerate(controls):
        row_y = card_y + 170 + i * 46
        key_surf = info_font.render(key,  True, COLOR_RED_HOVER)
        sep_surf = info_font.render("—",   True, COLOR_BLUE_ACCENT)
        val_surf = info_font.render(val,  True, COLOR_WHITE)
        screen.blit(key_surf, key_surf.get_rect(right=mid_x - 12, centery=row_y))
        screen.blit(sep_surf, sep_surf.get_rect(centerx=mid_x,    centery=row_y))
        screen.blit(val_surf, val_surf.get_rect(left=mid_x + 12,  centery=row_y))

    back_rect = draw_fancy_button("◀  BACK", SCREEN_WIDTH // 2,
                                  SETTINGS_BACK_BTN_Y, 240, 55, mouse_pos)
    return back_rect


def draw_victory_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((3, 4, 10, 210))
    screen.blit(overlay, (0, 0))
    draw_centered_text("YOU SAVED DUBLIN!",
                       font, COLOR_RED_HOVER, SCREEN_HEIGHT // 2 - 40)
    draw_centered_text("Press SPACE to return to the Menu",
                       subtitle_font, COLOR_CYAN_GLOW, SCREEN_HEIGHT // 2 + 20)


# ---------------------------------------------------------------------------
# Cutscene helpers
# ---------------------------------------------------------------------------

def play_cutscene(video_path):
    cutscene.play_video(screen, clock, video_path)


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------

def show_credits():
    credits.run_credits(screen, clock)


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------

def run_campaign():
    play_cutscene(INTRO_VIDEO)

    if lvl1.run_level() != "win":
        return
    if lvl2.run_level() != "win":
        return
    if lvl3.run_level() != "win":
        return

    play_cutscene(END_VIDEO)
    show_credits()


# ---------------------------------------------------------------------------
# Menu loop
# ---------------------------------------------------------------------------
clock = pygame.time.Clock()

while True:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == START:
                cx     = SCREEN_WIDTH // 2
                btn_w, btn_h = 280, 60
                start_r    = pygame.Rect(cx - btn_w // 2, 360 - btn_h // 2, btn_w, btn_h)
                settings_r = pygame.Rect(cx - btn_w // 2, 445 - btn_h // 2, btn_w, btn_h)
                quit_r     = pygame.Rect(cx - btn_w // 2, 530 - btn_h // 2, btn_w, btn_h)
                if start_r.collidepoint(mouse_pos):
                    run_campaign()
                    game_state = VICTORY
                elif settings_r.collidepoint(mouse_pos):
                    game_state = SETTINGS
                elif quit_r.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
            elif game_state == SETTINGS:
                back_r = pygame.Rect(
                    SCREEN_WIDTH // 2 - 120,
                    SETTINGS_BACK_BTN_Y - 27, 240, 55)
                if back_r.collidepoint(mouse_pos):
                    game_state = START

        if event.type == pygame.KEYDOWN:
            if game_state == VICTORY and event.key == pygame.K_SPACE:
                game_state = START

    if game_state == START:
        draw_start_screen(mouse_pos)
    elif game_state == SETTINGS:
        draw_settings_screen(mouse_pos)
    elif game_state == VICTORY:
        draw_victory_screen(mouse_pos)

    pygame.display.flip()
    clock.tick(60)