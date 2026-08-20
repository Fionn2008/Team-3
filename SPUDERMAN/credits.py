"""
Spuderman: Far From Dublin — End Credits (pygame)

Auto-scrolling credits roll drawn directly into the game's existing pygame
window (same screen/clock Main.py already owns), so it plays inline right
after the ending cutscene instead of opening a separate Tkinter window.
"""

import math
import random
import sys

import pygame

if not pygame.font.get_init():
    pygame.font.init()

W, H = 1280, 720
SCROLL_SPEED = 80.0  # pixels per second

RED       = (204, 17, 17)
RED2      = (255, 34, 34)
BLUE      = (26, 42, 138)
CITY_BLD  = (7, 10, 20)
AMBER     = (184, 128, 16)

SKY_STOPS = [
    (0.00, (3, 4, 10)),
    (0.45, (6, 8, 20)),
    (0.60, (10, 12, 28)),
    (0.70, (11, 14, 24)),
    (0.85, (16, 19, 30)),
    (1.00, (8, 9, 15)),
]

COURIER_PATH = (pygame.font.match_font("couriernew")
                or pygame.font.match_font("consolas")
                or pygame.font.get_default_font())
EMOJI_PATH   = pygame.font.match_font("segoeuiemoji")
EMOJI_CHARS  = set("\U0001F577\U0001F578✦")   # spider, web, star


# ══════════════════════════════════════════════════════
#  Credits DATA
# ══════════════════════════════════════════════════════
THANK_YOU_TEXT = (
    "From everyone on the team — thank you for swinging\n"
    "through Dublin with us.\n\n"
    "We hope Spuderman's adventure made you laugh,\n"
    "kept you on the edge of your seat, and maybe even\n"
    "made you crave a potato or two along the way.\n\n"
    "Every web shot, every dodge, every moment you spent\n"
    "in our world means everything to us.\n\n"
    "Until the next adventure — stay spectacular."
)

CREDITS = [
    ("Web Designer",                    "Reesa Kochumuttam"),
    ("Game Designer & Animator",        "Kyle Fahy"),
    ("Graphic Designer & Animator",     "Fionn O'Brien"),
    ("Game Designer",                   "Vedhasree Loganathan"),
    ("Game Designer",                   "Shahreen Prante"),
]

SPECIAL = [
    ("Everyone Who Played",             "You \U0001F577"),
    ("Built With",                      "Python"),
    ("Inspired By",                     "The Amazing Spider-Man\n& The Humble Potato"),
]


# ---------------------------------------------------------------------------
# Font / text helpers
# ---------------------------------------------------------------------------

_font_cache = {}


def _font(size, bold=False):
    key = (size, bold)
    f = _font_cache.get(key)
    if f is None:
        f = pygame.font.Font(COURIER_PATH, size)
        f.bold = bold
        _font_cache[key] = f
    return f


_emoji_font_cache = {}


def _emoji_font(size):
    f = _emoji_font_cache.get(size)
    if f is None:
        f = pygame.font.Font(EMOJI_PATH, size) if EMOJI_PATH else _font(size)
        _emoji_font_cache[size] = f
    return f


def _render_run(text, size, bold, color):
    """Render text that may mix normal glyphs with emoji (Courier New has
    no glyphs for the spider/web/star symbols, so those fall back to
    Segoe UI Emoji, run by run)."""
    if not text:
        return pygame.Surface((0, size), pygame.SRCALPHA)

    runs = []
    cur_kind, cur_chars = None, []
    for ch in text:
        kind = "emoji" if ch in EMOJI_CHARS else "text"
        if kind != cur_kind:
            if cur_chars:
                runs.append((cur_kind, "".join(cur_chars)))
                cur_chars = []
            cur_kind = kind
        cur_chars.append(ch)
    if cur_chars:
        runs.append((cur_kind, "".join(cur_chars)))

    pieces = [(_emoji_font(size) if kind == "emoji" else _font(size, bold)).render(chunk, True, color)
              for kind, chunk in runs]

    total_w = sum(p.get_width() for p in pieces)
    total_h = max((p.get_height() for p in pieces), default=size)
    combo = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
    x = 0
    for p in pieces:
        combo.blit(p, (x, (total_h - p.get_height()) // 2))
        x += p.get_width()
    return combo


def _render_multiline(text, size, bold, color, line_gap=4):
    lines = text.split("\n")
    surfs = [_render_run(line, size, bold, color) for line in lines]
    w = max(s.get_width() for s in surfs)
    total_h = sum(s.get_height() for s in surfs) + line_gap * (len(surfs) - 1)
    combo = pygame.Surface((w, total_h), pygame.SRCALPHA)
    y = 0
    for s in surfs:
        combo.blit(s, ((w - s.get_width()) // 2, y))
        y += s.get_height() + line_gap
    return combo


def _render_glow_text(text, size, bold, color, shadow_color):
    base = _render_run(text, size, bold, color)
    shadow = _render_run(text, size, bold, shadow_color)
    pad = 3
    combo = pygame.Surface((base.get_width() + pad * 2, base.get_height() + pad * 2), pygame.SRCALPHA)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        combo.blit(shadow, (pad + dx, pad + dy))
    combo.blit(base, (pad, pad))
    return combo


# ---------------------------------------------------------------------------
# Background art (pre-rendered once — cheap to blit every frame)
# ---------------------------------------------------------------------------

def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _draw_sky(surf, cw, ch):
    sky_bottom = int(ch * 0.50)
    n = 50
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        y0, y1 = int(t0 * sky_bottom), int(t1 * sky_bottom)
        col = SKY_STOPS[-1][1]
        for j in range(len(SKY_STOPS) - 1):
            if SKY_STOPS[j][0] <= t0 < SKY_STOPS[j + 1][0]:
                seg_t = (t0 - SKY_STOPS[j][0]) / (SKY_STOPS[j + 1][0] - SKY_STOPS[j][0])
                col = _lerp_color(SKY_STOPS[j][1], SKY_STOPS[j + 1][1], seg_t)
                break
        pygame.draw.rect(surf, col, (0, y0, cw, y1 - y0 + 1))
    pygame.draw.rect(surf, (8, 9, 15), (0, sky_bottom, cw, ch - sky_bottom))

    cx, cy = cw // 2, int(ch * 0.46)
    gw, gh = int(cw * 0.8), int(ch * 0.08)
    for i in range(20, 0, -1):
        t = i / 20
        col = (0x41, int(14 * t), int(8 * t))
        rect = pygame.Rect(0, 0, int(gw * 2 * t), int(gh * 2 * t))
        rect.center = (cx, cy)
        pygame.draw.ellipse(surf, col, rect)


def _draw_windows(surf, x1, y1, x2, y2):
    row_h = 11
    for ry in range(y1 + 4, y2 - 4, row_h):
        pygame.draw.rect(surf, (33, 26, 8), (x1 + 2, ry, max(1, x2 - x1 - 4), 3))


def _draw_skyline(surf, cw, ch):
    horizon = int(ch * 0.50)
    buildings_left = [
        (22, 0.54), (18, 0.72), (26, 0.43), (4, 0.20),
        (20, 0.83), (24, 0.59), (16, 0.91), (22, 0.67),
        (28, 0.49), (18, 0.77), (24, 0.62), (16, 0.54),
    ]
    buildings_right = [
        (16, 0.62), (22, 0.55), (18, 0.81), (26, 0.47),
        (20, 0.73), (24, 0.61), (18, 0.89), (28, 0.51),
        (24, 0.71), (20, 0.57), (14, 0.44),
    ]
    bh = int(ch * 0.12)

    x = 0
    for bw, hfrac in buildings_left:
        bh_px = int(bh * hfrac)
        pygame.draw.rect(surf, CITY_BLD, (x, horizon - bh_px, bw, bh_px))
        _draw_windows(surf, x, horizon - bh_px, x + bw, horizon)
        x += bw

    x = cw
    for bw, hfrac in buildings_right:
        bh_px = int(bh * hfrac)
        pygame.draw.rect(surf, CITY_BLD, (x - bw, horizon - bh_px, bw, bh_px))
        _draw_windows(surf, x - bw, horizon - bh_px, x, horizon)
        x -= bw


def _draw_road(surf, cw, ch):
    horizon = int(ch * 0.50)
    pygame.draw.polygon(surf, (16, 19, 30), [(0, ch), (cw, ch), (cw, horizon), (0, horizon)])
    vanish_x = cw // 2
    pygame.draw.line(surf, AMBER, (vanish_x - 2, horizon), (vanish_x - 10, ch), 2)
    pygame.draw.line(surf, AMBER, (vanish_x + 2, horizon), (vanish_x + 10, ch), 2)


def _draw_tower_base(surf, cw, ch):
    horizon = int(ch * 0.50)
    tw = min(int(cw * 0.07), 72)
    tx = cw // 2 - tw // 2
    tower_top = int(ch * 0.02)

    for i in range(tw):
        t = i / max(1, tw)
        col = _lerp_color((12, 22, 38), (22, 35, 54), abs(t - 0.5) * 2)
        pygame.draw.line(surf, col, (tx + i, tower_top), (tx + i, horizon))

    arch_w = int(tw * 0.44)
    arch_h = int((horizon - tower_top) * 0.35)
    ax = cw // 2 - arch_w // 2
    ay = horizon - arch_h
    bx1, by1, bx2, by2 = ax, ay, ax + arch_w, horizon + arch_h // 2
    ecx, ecy = (bx1 + bx2) / 2, (by1 + by2) / 2
    erx, ery = (bx2 - bx1) / 2, (by2 - by1) / 2
    pts = [(ecx + erx * math.cos(math.radians(deg)), ecy - ery * math.sin(math.radians(deg)))
           for deg in range(0, 181, 10)]
    pygame.draw.polygon(surf, (5, 8, 14), pts)


def _draw_cables(surf, cw, ch):
    cx = cw // 2
    top = int(ch * 0.04)
    angles_l = [-48, -62, -72, -80]
    angles_r = [48, 62, 72, 80]
    lengths  = [int(ch * 0.72), int(ch * 0.68), int(ch * 0.75), int(ch * 0.80)]
    widths   = [3, 2, 2, 2]
    col = (22, 32, 48)

    for ang, ln, wd in zip(angles_l, lengths, widths):
        rad = math.radians(ang)
        ex, ey = cx + math.sin(rad) * ln, top + math.cos(rad) * ln
        pygame.draw.line(surf, col, (cx, top), (ex, ey), wd)
    for ang, ln, wd in zip(angles_r, lengths, widths):
        rad = math.radians(ang)
        ex, ey = cx + math.sin(rad) * ln, top + math.cos(rad) * ln
        pygame.draw.line(surf, col, (cx, top), (ex, ey), wd)

    pygame.draw.line(surf, col, (int(cw * 0.02), int(ch * 0.08)), (int(cw * 0.78), ch), 2)
    pygame.draw.line(surf, col, (int(cw * 0.98), int(ch * 0.08)), (int(cw * 0.22), ch), 2)


def _build_base_layer(cw, ch):
    surf = pygame.Surface((cw, ch))
    _draw_sky(surf, cw, ch)
    _draw_skyline(surf, cw, ch)
    _draw_road(surf, cw, ch)
    _draw_tower_base(surf, cw, ch)
    _draw_cables(surf, cw, ch)
    return surf


def _draw_corner_web(surf, ox, oy, sx, sy):
    size = 180
    col = (204, 17, 17, 70)
    for ang in (0, 18, 36, 54, 72, 90):
        rad = math.radians(ang)
        ex = ox + sx * math.cos(rad) * size
        ey = oy + sy * math.sin(rad) * size
        pygame.draw.line(surf, col, (ox, oy), (ex, ey), 1)
    for dist in (40, 80, 120, 160):
        pts = [(ox + sx * math.cos(math.radians(ang)) * dist,
                oy + sy * math.sin(math.radians(ang)) * dist)
               for ang in range(0, 95, 5)]
        if len(pts) >= 2:
            pygame.draw.lines(surf, col, False, pts, 1)


def _build_overlay_layer(cw, ch):
    surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 90))

    for y in range(0, ch, 6):
        pygame.draw.rect(surf, (0, 0, 0, 70), (0, y + 3, cw, 1))

    fade_h = int(ch * 0.12)
    for i in range(fade_h):
        a = int(160 * (1 - i / fade_h))
        pygame.draw.rect(surf, (0, 0, 0, a), (0, i, cw, 1))
        pygame.draw.rect(surf, (0, 0, 0, a), (0, ch - 1 - i, cw, 1))

    for ox, oy, sx, sy in ((0, 0, 1, 1), (cw, 0, -1, 1), (0, ch, 1, -1), (cw, ch, -1, -1)):
        _draw_corner_web(surf, ox, oy, sx, sy)

    return surf


# ---------------------------------------------------------------------------
# Stars & beacon (animated every frame, drawn with cached sprites)
# ---------------------------------------------------------------------------

def _build_star_data():
    rng = random.Random(42)
    stars = []
    for _ in range(120):
        x = rng.randint(0, W)
        y = rng.randint(0, int(H * 0.55))
        r = rng.choice([0.5, 0.5, 1.0, 1.0, 1.5])
        alpha = rng.uniform(0.3, 1.0)
        warm = rng.random() < 0.12
        stars.append((x, y, r, alpha, warm))
    return stars


_star_sprites = {}


def _star_sprite(radius_px, warm):
    key = (radius_px, warm)
    sprite = _star_sprites.get(key)
    if sprite is None:
        d = radius_px * 2 + 2
        sprite = pygame.Surface((d, d), pygame.SRCALPHA)
        col = (255, 180, 180) if warm else (200, 208, 232)
        pygame.draw.circle(sprite, col, (d // 2, d // 2), radius_px)
        _star_sprites[key] = sprite
    return sprite


def _draw_stars(dest, stars, phase):
    twinkle = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(phase))
    for (x, y, r, base_alpha, warm) in stars:
        radius_px = max(1, round(r))
        sprite = _star_sprite(radius_px, warm)
        sprite.set_alpha(int(255 * min(1.0, base_alpha * twinkle)))
        dest.blit(sprite, (int(x - radius_px - 1), int(y - radius_px - 1)))


def _draw_beacon(dest, cw, ch, phase):
    tower_top = int(ch * 0.02)
    bx, by = cw // 2, tower_top - 6
    glow = 0.5 + 0.5 * math.sin(phase)
    brad = int(4 + glow * 6)

    glow_surf = pygame.Surface((brad * 4, brad * 4), pygame.SRCALPHA)
    alpha = int(255 * (0.4 + glow * 0.5))
    pygame.draw.circle(glow_surf, (255, 26, 26, alpha), (brad * 2, brad * 2), brad * 2)
    dest.blit(glow_surf, (bx - brad * 2, by - brad * 2))
    pygame.draw.circle(dest, (255, 34, 34), (bx, by), 4)


# ---------------------------------------------------------------------------
# Spider logo & thank-you box (pre-rendered surfaces)
# ---------------------------------------------------------------------------

def _build_spider_logo_surface():
    w, hgt = 140, 90
    surf = pygame.Surface((w, hgt), pygame.SRCALPHA)
    cx, cy = w // 2, hgt // 2 + 6

    pygame.draw.ellipse(surf, RED, (cx - 11, cy - 14, 22, 28))
    pygame.draw.ellipse(surf, RED, (cx - 9, cy - 36, 18, 18))

    legs = [
        ((-11, -12), (-35, -27)), ((-11, -5), (-36, -5)), ((-11, 2), (-35, 16)),
        ((11, -12), (35, -27)),   ((11, -5), (36, -5)),   ((11, 2), (35, 16)),
    ]
    for (sx, sy), (ex, ey) in legs:
        pygame.draw.line(surf, RED, (cx + sx, cy + sy), (cx + ex, cy + ey), 2)

    pygame.draw.ellipse(surf, (255, 255, 255), (cx - 8, cy - 32, 6, 6))
    pygame.draw.ellipse(surf, (255, 255, 255), (cx + 2, cy - 32, 6, 6))
    return surf


def _build_ty_box_surface(text, maxw):
    lines = text.split("\n")
    line_h = 22

    title_surf = _render_run("THANK YOU FOR PLAYING", 14, True, RED2)
    footer_surf = _render_run("— POTATO PRODUCTIONS \U0001F577", 9, False, (180, 30, 30))
    line_surfs = []
    for line in lines:
        if line == "":
            line_surfs.append(None)
            continue
        bold = line.startswith("Until") or line.startswith("From everyone")
        color = (255, 255, 255) if bold else (230, 210, 210)
        line_surfs.append(_render_run(line, 11, bold, color))

    body_h = sum(line_h if s is not None else line_h // 2 for s in line_surfs)
    total_h = 18 + title_surf.get_height() + 16 + body_h + 16 + footer_surf.get_height() + 14

    box = pygame.Surface((maxw, total_h), pygame.SRCALPHA)
    box.fill((0, 0, 0, 110))
    pygame.draw.rect(box, (92, 20, 20), box.get_rect(), width=1)

    spider_s = _render_run("\U0001F577", 13, False, RED)
    box.blit(spider_s, (14, 12))
    box.blit(spider_s, (maxw - 14 - spider_s.get_width(), 12))

    box.blit(title_surf, ((maxw - title_surf.get_width()) // 2, 18))

    ty = 18 + title_surf.get_height() + 16
    for s in line_surfs:
        if s is None:
            ty += line_h // 2
            continue
        box.blit(s, ((maxw - s.get_width()) // 2, ty))
        ty += line_h

    ty += 16
    box.blit(footer_surf, ((maxw - footer_surf.get_width()) // 2, ty))
    return box


# ---------------------------------------------------------------------------
# Credit line items
# ---------------------------------------------------------------------------

def _build_credit_items(maxw, ch):
    items = []

    def add(kind, h, **kw):
        items.append({"kind": kind, "h": h, **kw})

    def text_item(txt, size, bold, color, glow=None):
        surf = _render_glow_text(txt, size, bold, color, glow) if glow else _render_run(txt, size, bold, color)
        add("text", surf.get_height() + 14, surf=surf)

    add("spacer", 60)
    add("spider_logo", 90, surf=_build_spider_logo_surface())
    add("spacer", 14)

    text_item("POTATO PRODUCTIONS PRESENTS", 9, True, (204, 34, 34))
    add("spacer", 8)
    text_item("SPUDERMAN", 44, True, (255, 255, 255), glow=(136, 0, 0))
    text_item(":", 18, True, RED)
    text_item("FAR FROM", 22, False, (192, 168, 168))
    text_item("DUBLIN", 50, True, (255, 34, 34), glow=(255, 0, 0))
    add("divider", 18)

    add("spacer", 22)
    ty_surf = _build_ty_box_surface(THANK_YOU_TEXT, maxw)
    add("ty_box", ty_surf.get_height() + 20, surf=ty_surf)
    add("spacer", 38)

    add("section_hdr", 30, surf=_render_run("CREATED BY", 9, True, (200, 40, 40)))
    add("spacer", 10)

    for i, (role, name) in enumerate(CREDITS):
        role_surf = _render_run(role.upper(), 9, False, (200, 75, 75))
        name_surf = _render_multiline(name, 24, True, (240, 224, 224))
        add("credit", 16 + name_surf.get_height() + 18, role_surf=role_surf, name_surf=name_surf)
        if i < len(CREDITS) - 1:
            add("web_div", 28, surf=_render_run("\U0001F578", 12, False, (80, 21, 21)))

    add("spacer", 18)
    add("web_div", 28, surf=_render_run("✦", 12, False, (80, 21, 21)))
    add("section_hdr", 30, surf=_render_run("SPECIAL THANKS", 9, True, (200, 40, 40)))
    add("spacer", 10)

    for role, name in SPECIAL:
        role_surf = _render_run(role.upper(), 9, False, (200, 75, 75))
        name_surf = _render_multiline(name, 18, True, (240, 224, 224))
        add("credit", 16 + name_surf.get_height() + 18, role_surf=role_surf, name_surf=name_surf)
        add("spacer", 10)

    add("spacer", 30)
    add("divider", 18)
    add("spacer", 20)

    text_item("POTATO PRODUCTIONS", 13, False, RED)
    text_item("© 2026  ALL RIGHTS RESERVED", 9, False, (119, 112, 96))
    add("spacer", 14)
    text_item("\U0001F577", 24, False, RED)
    add("spacer", 10)
    text_item("NO POTATOES WERE HARMED IN THE MAKING OF THIS GAME", 8, False, (68, 56, 56))

    add("spacer", ch)  # let the last line fully clear the screen before finishing

    return items


def _draw_credits(dest, items, scroll_y, cx, ch, maxw):
    y_off = ch - scroll_y
    for item in items:
        h = item["h"]
        if y_off > ch + 150 or y_off + h < -150:
            y_off += h
            continue

        k = item["kind"]
        if k in ("text", "spider_logo", "ty_box"):
            surf = item["surf"]
            dest.blit(surf, (cx - surf.get_width() // 2, y_off))

        elif k == "divider":
            dw = min(180, maxw // 3)
            pygame.draw.line(dest, RED, (cx - dw, y_off + 6), (cx + dw, y_off + 6), 2)
            pygame.draw.line(dest, BLUE, (cx - dw, y_off + 8), (cx + dw, y_off + 8), 1)

        elif k == "section_hdr":
            surf = item["surf"]
            sw = 80
            pygame.draw.line(dest, (80, 16, 16), (cx - sw - 80, y_off + 10), (cx - sw, y_off + 10), 1)
            pygame.draw.line(dest, (80, 16, 16), (cx + sw, y_off + 10), (cx + sw + 80, y_off + 10), 1)
            dest.blit(surf, (cx - surf.get_width() // 2, y_off))

        elif k == "web_div":
            surf = item["surf"]
            pygame.draw.line(dest, (80, 21, 21), (cx - 200, y_off + 10), (cx - 18, y_off + 10), 1)
            pygame.draw.line(dest, (80, 21, 21), (cx + 18, y_off + 10), (cx + 200, y_off + 10), 1)
            dest.blit(surf, (cx - surf.get_width() // 2, y_off))

        elif k == "credit":
            role_surf, name_surf = item["role_surf"], item["name_surf"]
            dest.blit(role_surf, (cx - role_surf.get_width() // 2, y_off))
            dest.blit(name_surf, (cx - name_surf.get_width() // 2, y_off + 16))

        y_off += h


# ---------------------------------------------------------------------------
# UI chrome (pause button / skip hint) & fade-out
# ---------------------------------------------------------------------------

def _draw_pause_button(dest, rect, paused, font):
    pygame.draw.rect(dest, (18, 10, 10), rect, border_radius=8)
    pygame.draw.rect(dest, (150, 20, 20), rect, width=2, border_radius=8)
    label = font.render("RESUME" if paused else "PAUSE", True, (240, 200, 200))
    dest.blit(label, label.get_rect(center=rect.center))


def _draw_hint(dest, font, ch):
    label = font.render("SPACE / ESC  —  SKIP", True, (140, 60, 60))
    dest.blit(label, (18, ch - 34))


def _fade_out(screen, clock, duration_ms=500):
    snapshot = screen.copy()
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    start = pygame.time.get_ticks()
    while True:
        elapsed = pygame.time.get_ticks() - start
        if elapsed >= duration_ms:
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.blit(snapshot, (0, 0))
        veil.fill((0, 0, 0, int(255 * elapsed / duration_ms)))
        screen.blit(veil, (0, 0))
        pygame.display.flip()
        clock.tick(60)
    screen.fill((0, 0, 0))
    pygame.display.flip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

SKIP_KEYS = (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER)


def run_credits(screen, clock):
    cw, ch = screen.get_size()
    cx = cw // 2
    maxw = min(640, int(cw * 0.88))

    base_layer    = _build_base_layer(cw, ch)
    overlay_layer = _build_overlay_layer(cw, ch)
    stars         = _build_star_data()
    items         = _build_credit_items(maxw, ch)
    total_scroll  = sum(item["h"] for item in items)

    ui_font = pygame.font.Font(COURIER_PATH, 15)
    ui_font.bold = True
    pause_rect = pygame.Rect(cw - 168, ch - 58, 150, 38)

    scroll_y = 0.0
    twinkle_phase = 0.0
    beacon_phase  = 0.0
    paused = False

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key in SKIP_KEYS:
                _fade_out(screen, clock)
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pause_rect.collidepoint(event.pos):
                    paused = not paused

        if not paused:
            scroll_y += SCROLL_SPEED * dt
            if scroll_y >= total_scroll:
                _fade_out(screen, clock)
                return

        twinkle_phase = (twinkle_phase + 0.7 * dt) % (2 * math.pi)
        beacon_phase  = (beacon_phase + 1.4 * dt) % (2 * math.pi)

        screen.blit(base_layer, (0, 0))
        _draw_stars(screen, stars, twinkle_phase)
        _draw_beacon(screen, cw, ch, beacon_phase)
        screen.blit(overlay_layer, (0, 0))
        _draw_credits(screen, items, scroll_y, cx, ch, maxw)
        _draw_pause_button(screen, pause_rect, paused, ui_font)
        _draw_hint(screen, ui_font, ch)

        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    _screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Spuderman - Credits Preview")
    _clock = pygame.time.Clock()
    run_credits(_screen, _clock)
    pygame.quit()
