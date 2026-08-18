import pygame
import sys
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

# Import the levels *after* the display exists so each one reuses this
# window (via pygame.display.get_surface()) instead of creating its own.
import lvl1
import lvl2
import lvl3

# Fonts
font          = pygame.font.SysFont(None, 74)
subtitle_font = pygame.font.SysFont(None, 42)
info_font     = pygame.font.SysFont(None, 36)
button_font   = pygame.font.SysFont(None, 48)

# Background
start_bg_img = pygame.image.load(join(BASE_DIR, "images", "start screen.png")).convert()
start_bg_img = pygame.transform.scale(start_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Game state
START    = "start"
SETTINGS = "settings"
VICTORY  = "victory"
game_state = START

# Shared Y position for the Settings back button — used by both draw and click handler
SETTINGS_BACK_BTN_Y = 648


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def draw_centered_text(text, fnt, color, y):
    """Renders text centred horizontally at the given y position."""
    surface = fnt.render(text, True, color)
    r = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(surface, r)


def draw_fancy_button(text, cx, cy, w, h, mouse_pos):
    """
    Draws a stylised button with a dark semi-transparent panel, gold border,
    and a glow/highlight when hovered. Returns the button Rect.
    """
    btn_rect  = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    hovered   = btn_rect.collidepoint(mouse_pos)

    # Shadow
    shadow_rect = btn_rect.move(4, 4)
    shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 120), shadow_surf.get_rect(), border_radius=14)
    screen.blit(shadow_surf, shadow_rect.topleft)

    # Background panel
    panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    bg_alpha   = 210 if hovered else 170
    pygame.draw.rect(panel_surf, (15, 15, 30, bg_alpha), panel_surf.get_rect(), border_radius=14)
    screen.blit(panel_surf, btn_rect.topleft)

    # Gold border (brighter on hover)
    border_col = (255, 215, 0) if hovered else (180, 140, 0)
    pygame.draw.rect(screen, border_col, btn_rect, width=3, border_radius=14)

    # Inner highlight line at top
    hi_surf = pygame.Surface((w - 20, 3), pygame.SRCALPHA)
    hi_surf.fill((255, 255, 255, 60 if hovered else 30))
    screen.blit(hi_surf, (btn_rect.x + 10, btn_rect.y + 6))

    # Text — white with a dark drop shadow
    label_shadow = button_font.render(text, True, (0, 0, 0))
    label        = button_font.render(text, True, (255, 215, 0) if hovered else (230, 230, 230))
    lr = label.get_rect(center=(cx, cy))
    screen.blit(label_shadow, lr.move(2, 2))
    screen.blit(label, lr)

    return btn_rect


def draw_start_screen(mouse_pos):
    # Dublin skyline background
    screen.blit(start_bg_img, (0, 0))

    # Dark gradient overlay across the bottom half so buttons read clearly
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for row in range(SCREEN_HEIGHT):
        alpha = int(180 * max(0, (row - SCREEN_HEIGHT // 3)) / (SCREEN_HEIGHT * 2 // 3))
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, row), (SCREEN_WIDTH, row))
    screen.blit(overlay, (0, 0))

    # Title with layered shadow for depth
    title_text = "Spiderman"
    sub_text   = "Far From Dublin"

    # Outer glow / thick shadow
    for offset in range(5, 0, -1):
        shadow = font.render(title_text, True, (180, 0, 0))
        r = shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset, 140 + offset))
        screen.blit(shadow, r)

    title_surf = font.render(title_text, True, (255, 30, 30))
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 140))
    screen.blit(title_surf, title_rect)

    sub_surf = subtitle_font.render(sub_text, True, (255, 215, 0))
    sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 205))
    screen.blit(sub_surf, sub_rect)

    # Decorative divider line under the title
    pygame.draw.line(screen, (255, 215, 0),
                     (SCREEN_WIDTH // 2 - 220, 230),
                     (SCREEN_WIDTH // 2 + 220, 230), 2)

    # Buttons — stacked vertically in the lower centre
    btn_w, btn_h = 280, 60
    cx           = SCREEN_WIDTH // 2
    start_rect    = draw_fancy_button("▶  START",    cx, 360, btn_w, btn_h, mouse_pos)
    settings_rect = draw_fancy_button("⚙  SETTINGS", cx, 445, btn_w, btn_h, mouse_pos)
    quit_rect     = draw_fancy_button("✕  QUIT",     cx, 530, btn_w, btn_h, mouse_pos)

    return start_rect, settings_rect, quit_rect


def draw_settings_screen(mouse_pos):
    """Settings screen showing controls, with a centred card layout."""
    screen.blit(start_bg_img, (0, 0))

    # Full-screen dark overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    # ---- Centred card ----
    card_w, card_h = 700, 500
    card_x = SCREEN_WIDTH  // 2 - card_w // 2
    card_y = 90
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (10, 10, 25, 210), card_surf.get_rect(), border_radius=18)
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (180, 140, 0),
                     (card_x, card_y, card_w, card_h), width=2, border_radius=18)

    # Title
    draw_centered_text("Settings", font, (255, 215, 0), card_y + 52)

    # Gold divider
    pygame.draw.line(screen, (255, 215, 0),
                     (card_x + 40, card_y + 98),
                     (card_x + card_w - 40, card_y + 98), 1)

    # Controls sub-heading
    draw_centered_text("Controls", subtitle_font, (200, 200, 200), card_y + 128)

    controls = [
        ("A / D",         "Move Spiderman left and right"),
        ("SPACE",         "Jump / Shoot Webs (per level)"),
        ("Left Click",    "Attack  (must be in range)"),
        ("Chicken Roll",  "Walk over it to restore HP"),
        ("Enemy AI",      "Chases and auto-attacks you"),
        ("Win Condition", "Beat all 3 levels to finish"),
    ]

    # Two-column layout: key right-aligned | value left-aligned
    col_gap   = 24          # gap between key col-right edge and value col-left edge
    mid_x     = SCREEN_WIDTH // 2
    row_y_start = card_y + 170
    row_gap   = 46

    for i, (key, val) in enumerate(controls):
        row_y = row_y_start + i * row_gap

        # Key — right-aligned to mid_x - col_gap//2, gold
        key_surf = info_font.render(key, True, (255, 215, 0))
        key_rect = key_surf.get_rect(right=mid_x - col_gap // 2, centery=row_y)
        screen.blit(key_surf, key_rect)

        # Separator
        sep_surf = info_font.render("—", True, (130, 130, 130))
        sep_rect = sep_surf.get_rect(centerx=mid_x, centery=row_y)
        screen.blit(sep_surf, sep_rect)

        # Value — left-aligned from mid_x + col_gap//2, light grey
        val_surf = info_font.render(val, True, (215, 215, 215))
        val_rect = val_surf.get_rect(left=mid_x + col_gap // 2, centery=row_y)
        screen.blit(val_surf, val_rect)

    # Back button — anchored to a fixed Y so the click handler can match it exactly
    back_rect = draw_fancy_button("◀  BACK", SCREEN_WIDTH // 2, SETTINGS_BACK_BTN_Y, 240, 55, mouse_pos)
    return back_rect


def draw_victory_screen(mouse_pos):
    """Shown once all three levels have been beaten."""
    screen.blit(start_bg_img, (0, 0))

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    draw_centered_text("YOU SAVED DUBLIN!", font, (255, 215, 0), SCREEN_HEIGHT // 2 - 40)
    draw_centered_text("Press SPACE to return to the Menu", subtitle_font, (255, 255, 255), SCREEN_HEIGHT // 2 + 20)


def run_campaign():
    """
    Runs Level 1 -> Level 2 -> Level 3 in sequence. Each run_level() call
    blocks until that level is won (it returns "win") or the window is
    closed (it exits the process directly). Stops early if a level is
    quit some other way instead of being won.
    """
    if lvl1.run_level() != "win":
        return
    if lvl2.run_level() != "win":
        return
    lvl3.run_level()


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
                btn_w, btn_h = 280, 60
                cx = SCREEN_WIDTH // 2
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
                back_r = pygame.Rect(SCREEN_WIDTH // 2 - 120, SETTINGS_BACK_BTN_Y - 27, 240, 55)
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
