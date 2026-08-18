import pygame
import sys
import webbrowser
from os.path import join, dirname, abspath

# Initialize Pygame
pygame.init()

# All asset paths are resolved relative to this file's own folder,
# so the game runs correctly regardless of the working directory.
BASE_DIR = dirname(abspath(__file__))

# Screen setup
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spiderman - Far From Dublin")

# Import levels after the display exists so each one reuses this window
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

# Cutscene slides
CUTSCENE_DIR    = join(BASE_DIR, "images", "CutScenes")
INTRO_SLIDES    = range(1,  6)   # before Level 1
PRE_LVL3_SLIDES = range(6,  14)  # before Level 3
END_SLIDES      = range(14, 19)  # after Level 3

# Game states
START    = "start"
SETTINGS = "settings"
VICTORY  = "victory"
game_state = START

# Shared Y for the Settings back button
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

    # Shadow
    shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 120),
                     shadow_surf.get_rect(), border_radius=14)
    screen.blit(shadow_surf, btn_rect.move(4, 4).topleft)

    # Panel
    panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (15, 15, 30, 210 if hovered else 170),
                     panel_surf.get_rect(), border_radius=14)
    screen.blit(panel_surf, btn_rect.topleft)

    # Border
    pygame.draw.rect(screen,
                     (255, 215, 0) if hovered else (180, 140, 0),
                     btn_rect, width=3, border_radius=14)

    # Top highlight
    hi = pygame.Surface((w - 20, 3), pygame.SRCALPHA)
    hi.fill((255, 255, 255, 60 if hovered else 30))
    screen.blit(hi, (btn_rect.x + 10, btn_rect.y + 6))

    # Text
    label_shadow = button_font.render(text, True, (0, 0, 0))
    label        = button_font.render(text, True,
                                      (255, 215, 0) if hovered else (230, 230, 230))
    lr = label.get_rect(center=(cx, cy))
    screen.blit(label_shadow, lr.move(2, 2))
    screen.blit(label, lr)

    return btn_rect


def draw_start_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for row in range(SCREEN_HEIGHT):
        alpha = int(180 * max(0, (row - SCREEN_HEIGHT // 3)) / (SCREEN_HEIGHT * 2 // 3))
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, row), (SCREEN_WIDTH, row))
    screen.blit(overlay, (0, 0))

    for offset in range(5, 0, -1):
        shadow = font.render("Spiderman", True, (180, 0, 0))
        r = shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset, 140 + offset))
        screen.blit(shadow, r)

    title_surf = font.render("Spiderman", True, (255, 30, 30))
    screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 140)))

    sub_surf = subtitle_font.render("Far From Dublin", True, (255, 215, 0))
    screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 205)))

    pygame.draw.line(screen, (255, 215, 0),
                     (SCREEN_WIDTH // 2 - 220, 230),
                     (SCREEN_WIDTH // 2 + 220, 230), 2)

    cx = SCREEN_WIDTH // 2
    start_rect    = draw_fancy_button("▶  START",    cx, 360, 280, 60, mouse_pos)
    settings_rect = draw_fancy_button("⚙  SETTINGS", cx, 445, 280, 60, mouse_pos)
    quit_rect     = draw_fancy_button("✕  QUIT",     cx, 530, 280, 60, mouse_pos)
    return start_rect, settings_rect, quit_rect


def draw_settings_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    card_w, card_h = 700, 500
    card_x = SCREEN_WIDTH  // 2 - card_w // 2
    card_y = 90
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (10, 10, 25, 210),
                     card_surf.get_rect(), border_radius=18)
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (180, 140, 0),
                     (card_x, card_y, card_w, card_h), width=2, border_radius=18)

    draw_centered_text("Settings",  font,          (255, 215, 0),   card_y + 52)
    pygame.draw.line(screen, (255, 215, 0),
                     (card_x + 40, card_y + 98),
                     (card_x + card_w - 40, card_y + 98), 1)
    draw_centered_text("Controls", subtitle_font,  (200, 200, 200), card_y + 128)

    controls = [
        ("A / D",         "Move Spiderman left and right"),
        ("SPACE",         "Jump / Shoot Webs (per level)"),
        ("Left Click",    "Attack  (must be in range)"),
        ("Chicken Roll",  "Walk over it to restore HP"),
        ("Enemy AI",      "Chases and auto-attacks you"),
        ("Win Condition", "Beat all 3 levels to finish"),
    ]
    mid_x = SCREEN_WIDTH // 2
    for i, (key, val) in enumerate(controls):
        row_y = card_y + 170 + i * 46
        key_surf = info_font.render(key,  True, (255, 215, 0))
        sep_surf = info_font.render("—",   True, (130, 130, 130))
        val_surf = info_font.render(val,  True, (215, 215, 215))
        screen.blit(key_surf, key_surf.get_rect(right=mid_x - 12,   centery=row_y))
        screen.blit(sep_surf, sep_surf.get_rect(centerx=mid_x,      centery=row_y))
        screen.blit(val_surf, val_surf.get_rect(left=mid_x  + 12,   centery=row_y))

    back_rect = draw_fancy_button("◀  BACK", SCREEN_WIDTH // 2,
                                  SETTINGS_BACK_BTN_Y, 240, 55, mouse_pos)
    return back_rect


def draw_victory_screen(mouse_pos):
    screen.blit(start_bg_img, (0, 0))
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    draw_centered_text("YOU SAVED DUBLIN!",
                       font, (255, 215, 0), SCREEN_HEIGHT // 2 - 40)
    draw_centered_text("Press SPACE to return to the Menu",
                       subtitle_font, (255, 255, 255), SCREEN_HEIGHT // 2 + 20)


# ---------------------------------------------------------------------------
# Cutscene helpers
# ---------------------------------------------------------------------------

def _pump_quit_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def _fade_slide(slide_img, from_alpha, to_alpha, duration_ms):
    start = pygame.time.get_ticks()
    while True:
        _pump_quit_events()
        elapsed  = pygame.time.get_ticks() - start
        if elapsed >= duration_ms:
            break
        progress = elapsed / duration_ms
        alpha    = int(from_alpha + (to_alpha - from_alpha) * progress)
        screen.fill((0, 0, 0))
        slide_img.set_alpha(alpha)
        screen.blit(slide_img, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def _hold_slide(slide_img, duration_ms):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        _pump_quit_events()
        screen.blit(slide_img, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def play_cutscene(slide_numbers, hold_ms=2000, fade_ms=500):
    for n in slide_numbers:
        slide_img = pygame.image.load(
            join(CUTSCENE_DIR, f"Slide{n}.PNG")).convert()
        slide_img = pygame.transform.scale(
            slide_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        _fade_slide(slide_img, 0,   255, fade_ms)
        slide_img.set_alpha(255)
        _hold_slide(slide_img, hold_ms)
        _fade_slide(slide_img, 255, 0,   fade_ms)


# ---------------------------------------------------------------------------
# Credits  — opens credits-pure.html in the browser, then shows a
#            "Credits are open in your browser" holding screen in Pygame
#            until the player presses SPACE or closes the window.
# ---------------------------------------------------------------------------

def show_credits():
    """
    After the end cutscene, open the Spider-Man credits page in the
    default browser. Meanwhile keep the Pygame window alive with a
    simple holding screen so the process doesn't just exit.
    """
    credits_path = join(BASE_DIR, "credits-pure.html")
    # webbrowser.open accepts a local file path; prefix with file:// on all platforms
    webbrowser.open("file:///" + credits_path.replace("\\", "/"))

    # ── Holding screen ───────────────────────────────────────
    holding = True
    while holding:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                holding = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if they clicked the "Return to Menu" button
                btn_rect = pygame.Rect(
                    SCREEN_WIDTH // 2 - 160,
                    SCREEN_HEIGHT // 2 + 80,
                    320, 55
                )
                if btn_rect.collidepoint(mouse_pos):
                    holding = False

        # Draw a simple dark screen with instruction text
        screen.fill((4, 4, 12))

        # Spider logo (drawn with basic shapes — no external asset needed)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 130
        # Body
        pygame.draw.ellipse(screen, (180, 10, 10),
                            (cx - 16, cy - 4, 32, 40))
        pygame.draw.ellipse(screen, (180, 10, 10),
                            (cx - 12, cy - 24, 24, 24))
        # Eyes
        pygame.draw.ellipse(screen, (255, 255, 255),
                            (cx - 12, cy - 22, 8, 6))
        pygame.draw.ellipse(screen, (255, 255, 255),
                            (cx + 4,  cy - 22, 8, 6))
        # Legs
        legs = [
            ((cx - 16, cy + 2),  (cx - 55, cy - 30)),
            ((cx - 16, cy + 10), (cx - 58, cy + 10)),
            ((cx - 16, cy + 18), (cx - 55, cy + 42)),
            ((cx + 16, cy + 2),  (cx + 55, cy - 30)),
            ((cx + 16, cy + 10), (cx + 58, cy + 10)),
            ((cx + 16, cy + 18), (cx + 55, cy + 42)),
        ]
        for p1, p2 in legs:
            pygame.draw.line(screen, (180, 10, 10), p1, p2, 3)

        # Title text
        t1 = font.render("SPUDERMAN", True, (255, 40, 40))
        screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
        t2 = subtitle_font.render("FAR FROM DUBLIN", True, (200, 60, 60))
        screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))

        # Divider
        pygame.draw.line(screen, (140, 10, 10),
                         (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 35),
                         (SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 + 35), 1)

        # Credits open message
        msg = info_font.render(
            "Credits are open in your browser  🕷", True, (200, 160, 160))
        screen.blit(msg, msg.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 58)))

        # Return to menu button
        draw_fancy_button("▶  RETURN TO MENU",
                          SCREEN_WIDTH  // 2,
                          SCREEN_HEIGHT // 2 + 108,
                          320, 55, mouse_pos)

        hint = info_font.render(
            "or press  SPACE", True, (100, 80, 80))
        screen.blit(hint, hint.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)))

        pygame.display.flip()
        clock.tick(60)


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------

def run_campaign():
    """
    Full campaign flow:
      intro cutscene → Level 1 → Level 2 →
      pre-boss cutscene → Level 3 →
      end cutscene → Credits (browser)
    """
    play_cutscene(INTRO_SLIDES)

    if lvl1.run_level() != "win":
        return
    if lvl2.run_level() != "win":
        return

    play_cutscene(PRE_LVL3_SLIDES)

    if lvl3.run_level() != "win":
        return

    # End cutscene plays, THEN credits open
    play_cutscene(END_SLIDES)
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
