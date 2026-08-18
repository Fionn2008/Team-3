"""
Spuderman: Far From Dublin — End Credits
Converted from HTML/CSS to Python (tkinter)
"""

import tkinter as tk
import math
import random

# ── Colours ─────────────────────────────────────────
RED      = "#cc1111"
RED2     = "#ff2222"
RED3     = "#8b0000"
BLUE     = "#1a2a8a"
WHITE    = "#f0e8e8"
BG_DARK  = "#03040a"
DARK_NAV = "#060814"
CITY_BLD = "#070a14"
AMBER    = "#b88010"

W, H = 1280, 720          # window size
SCROLL_SPEED = 3         # pixels per frame (lower = slower)
FPS          = 60

# ══════════════════════════════════════════════════════
#  Helper: interpolate two hex colours
# ══════════════════════════════════════════════════════
def lerp_color(c1, c2, t):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

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
    ("Everyone Who Played",             "You 🕷"),
    ("Built With",                      "Python"),
    ("Inspired By",                     "The Amazing Spider-Man\n& The Humble Potato"),
]

# ══════════════════════════════════════════════════════
#  Application
# ══════════════════════════════════════════════════════
class CreditsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Spuderman: Far From Dublin — End Credits")
        self.root.configure(bg="#000")
        self.root.resizable(True, True)

        # Canvas
        self.canvas = tk.Canvas(root, width=W, height=H,
                                bg=BG_DARK, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.paused   = False
        self.scroll_y = 0.0

        # Animation phases
        self.twinkle_phase = 0.0
        self.beacon_phase  = 0.0

        # Background assets
        self.star_data = []
        self._build_stars()

        # Build credit lines
        self.credit_lines = []
        self._build_credit_lines()

        # Total scroll distance
        self.total_scroll = self._measure_credits_height() + H

        # Pause button
        self.pause_btn = tk.Button(
            root, text="⏸  PAUSE",
            font=("Courier", 9, "bold"),
            bg="#820808", fg="#ffaaaa",
            activebackground="#be0f0f", activeforeground="#fff",
            relief=tk.FLAT, padx=12, pady=5,
            cursor="hand2",
            command=self._toggle_pause
        )
        self.pause_btn.place(relx=1.0, rely=1.0, anchor="se", x=-18, y=-18)

        hint = tk.Label(root, text="CLICK TO PAUSE / RESUME",
                        font=("Courier", 7), fg="#551111", bg=BG_DARK)
        hint.place(x=18, rely=1.0, anchor="sw", y=-20)

        # Start render loop
        self._loop()

    def _build_stars(self):
        random.seed(42)
        self.star_data = []
        for _ in range(120):
            x     = random.randint(0, W)
            y     = random.randint(0, int(H * 0.55))
            r     = random.choice([0.5, 0.5, 1.0, 1.0, 1.5])
            alpha = random.uniform(0.3, 1.0)
            warm  = random.random() < 0.12
            self.star_data.append((x, y, r, alpha, warm))

    def _build_credit_lines(self):
        lines = self.credit_lines
        lines.clear()

        def add(kind, **kw):
            lines.append({"kind": kind, **kw})

        add("spacer", h=60)
        add("spider_logo", h=90)
        add("spacer", h=14)
        add("text", txt="POTATO PRODUCTIONS PRESENTS",
            font=("Courier", 9, "bold"), fill="#cc2222")
        add("spacer", h=8)
        add("text", txt="SPUDERMAN",
            font=("Courier", 44, "bold"), fill="#ffffff",
            shadow="#cc1111", glow=True)
        add("text", txt=":",
            font=("Courier", 18, "bold"), fill="#cc1111")
        add("text", txt="FAR FROM",
            font=("Courier", 22), fill="#c0a8a8")
        add("text", txt="DUBLIN",
            font=("Courier", 50, "bold"), fill="#ff2222",
            shadow="#ff0000", glow=True)
        add("divider_line", h=18)

        # Thank-you block
        add("spacer", h=22)
        add("ty_box", text=THANK_YOU_TEXT)
        add("spacer", h=38)

        # Credits
        add("section_hdr", txt="CREATED BY")
        add("spacer", h=10)

        for i, (role, name) in enumerate(CREDITS):
            add("credit", role=role, name=name)
            if i < len(CREDITS) - 1:
                add("web_div")

        # Special thanks
        add("spacer", h=18)
        add("web_div", symbol="✦")
        add("section_hdr", txt="SPECIAL THANKS")
        add("spacer", h=10)

        for role, name in SPECIAL:
            add("credit", role=role, name=name, small=True)
            add("spacer", h=10)

        # End card
        add("spacer", h=30)
        add("divider_line", h=0)
        add("spacer", h=20)
        add("text", txt="POTATO PRODUCTIONS",
            font=("Courier", 13), fill="#cc1111")
        add("text", txt="© 2026  ALL RIGHTS RESERVED",
            font=("Courier", 9), fill="#777060")
        add("spacer", h=14)
        add("text", txt="🕷", font=("Courier", 24), fill="#cc1111")
        add("spacer", h=10)
        add("text", txt="NO POTATOES WERE HARMED IN THE MAKING OF THIS GAME",
            font=("Courier", 8), fill="#443838")
        add("spacer", h=H + 40)

    def _measure_credits_height(self):
        total = 0
        for item in self.credit_lines:
            total += self._item_height(item)
        return total

    def _loop(self):
        if not self.paused:
            self.scroll_y += SCROLL_SPEED
            if self.scroll_y >= self.total_scroll:
                self.scroll_y = 0.0

        self.twinkle_phase = (self.twinkle_phase + 0.018) % (2 * math.pi)
        self.beacon_phase  = (self.beacon_phase  + 0.035) % (2 * math.pi)

        self._draw()
        self.root.after(int(1000 / FPS), self._loop)

    def _draw(self):
        c  = self.canvas
        cw = c.winfo_width()
        ch = c.winfo_height()

        if cw <= 1 or ch <= 1:
            cw, ch = W, H

        c.delete("all")

        self._draw_sky(c, cw, ch)
        self._draw_stars(c, cw, ch)
        self._draw_skyline(c, cw, ch)
        self._draw_road(c, cw, ch)
        self._draw_tower(c, cw, ch)
        self._draw_cables(c, cw, ch)
        self._draw_scanlines(c, cw, ch)

        # Dark overlay for text contrast
        c.create_rectangle(0, 0, cw, ch, fill="#000000", stipple="gray50", outline="")

        self._draw_fade(c, cw, ch)
        self._draw_corner_web(c, 0,  0,   1,  1)
        self._draw_corner_web(c, cw, 0,  -1,  1)
        self._draw_corner_web(c, 0,  ch,  1, -1)
        self._draw_corner_web(c, cw, ch, -1, -1)

        self._draw_credits(c, cw, ch)

    def _draw_sky(self, c, cw, ch):
        sky_bottom = int(ch * 0.50)
        stops = [
            (0.00, "#03040a"),
            (0.45, "#060814"),
            (0.60, "#0a0c1c"),
            (0.70, "#0b0e18"),
            (0.85, "#10131e"),
            (1.00, "#08090f"),
        ]
        n = 50
        for i in range(n):
            t0 = i / n
            t1 = (i + 1) / n
            y0 = int(t0 * sky_bottom)
            y1 = int(t1 * sky_bottom)
            col = stops[-1][1]
            for j in range(len(stops) - 1):
                if stops[j][0] <= t0 < stops[j+1][0]:
                    seg_t = (t0 - stops[j][0]) / (stops[j+1][0] - stops[j][0])
                    col   = lerp_color(stops[j][1], stops[j+1][1], seg_t)
                    break
            c.create_rectangle(0, y0, cw, y1+1, fill=col, outline="")

        c.create_rectangle(0, sky_bottom, cw, ch, fill="#08090f", outline="")

        cx, cy = cw // 2, int(ch * 0.46)
        gw, gh = int(cw * 0.8), int(ch * 0.08)
        for i in range(20, 0, -1):
            t = i / 20
            col = f"#41{format(int(14*t),'02x')}{format(int(8*t),'02x')}"
            c.create_oval(
                cx - int(gw * t), cy - int(gh * t),
                cx + int(gw * t), cy + int(gh * t),
                fill=col, outline=""
            )

    def _draw_stars(self, c, cw, ch):
        twinkle = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self.twinkle_phase))
        for (sx, sy, r, base_alpha, warm) in self.star_data:
            x = int(sx / W * cw)
            y = int(sy / (H * 0.55) * ch * 0.45)
            a = base_alpha * twinkle
            col = self._alpha_color("#ffb4b4" if warm else "#c8d0e8", a)
            c.create_oval(x-r, y-r, x+r, y+r, fill=col, outline="")

    def _draw_skyline(self, c, cw, ch):
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
        for (bw, hfrac) in buildings_left:
            bh_px = int(bh * hfrac)
            c.create_rectangle(x, horizon - bh_px, x + bw, horizon,
                               fill=CITY_BLD, outline="")
            self._draw_windows(c, x, horizon - bh_px, x + bw, horizon)
            x += bw

        x = cw
        for (bw, hfrac) in buildings_right:
            bh_px = int(bh * hfrac)
            c.create_rectangle(x - bw, horizon - bh_px, x, horizon,
                               fill=CITY_BLD, outline="")
            self._draw_windows(c, x - bw, horizon - bh_px, x, horizon)
            x -= bw

    def _draw_windows(self, c, x1, y1, x2, y2):
        row_h = 11
        for ry in range(y1 + 4, y2 - 4, row_h):
            c.create_rectangle(x1 + 2, ry, x2 - 2, ry + 3,
                               fill="#211a08", outline="")

    def _draw_road(self, c, cw, ch):
        horizon = int(ch * 0.50)
        c.create_polygon(0, ch, cw, ch, cw, horizon, 0, horizon,
                         fill="#10131e", outline="")
        vanish_x = cw // 2
        c.create_line(vanish_x - 2, horizon, vanish_x - 10, ch, fill=AMBER, width=2)
        c.create_line(vanish_x + 2, horizon, vanish_x + 10, ch, fill=AMBER, width=2)

    def _draw_tower(self, c, cw, ch):
        horizon = int(ch * 0.50)
        tw = min(int(cw * 0.07), 72)
        tx = cw // 2 - tw // 2
        tower_top = int(ch * 0.02)
        
        for i in range(tw):
            t = i / max(1, tw)
            col = lerp_color("#0c1626", "#162336", abs(t - 0.5) * 2)
            c.create_line(tx + i, tower_top, tx + i, horizon, fill=col)

        arch_w = int(tw * 0.44)
        arch_h = int((horizon - tower_top) * 0.35)
        ax = cw // 2 - arch_w // 2
        ay = horizon - arch_h
        c.create_arc(ax, ay, ax + arch_w, horizon + arch_h // 2,
                     start=0, extent=180, fill="#05080e", outline="")

        bx = cw // 2
        by = tower_top - 6
        glow = 0.5 + 0.5 * math.sin(self.beacon_phase)
        brad = int(4 + glow * 6)
        bg_col = self._alpha_color("#ff1a1a", 0.4 + glow * 0.5)
        c.create_oval(bx - brad*2, by - brad*2, bx + brad*2, by + brad*2,
                     fill=bg_col, outline="")
        c.create_oval(bx - 4, by - 4, bx + 4, by + 4, fill="#ff2222", outline="")

    def _draw_cables(self, c, cw, ch):
        cx  = cw // 2
        top = int(ch * 0.04)
        angles_l = [-48, -62, -72, -80]
        angles_r = [ 48,  62,  72,  80]
        lengths  = [int(ch * 0.72), int(ch * 0.68), int(ch * 0.75), int(ch * 0.80)]
        widths   = [3, 2.5, 2, 2]

        for ang, ln, wd in zip(angles_l, lengths, widths):
            rad = math.radians(ang)
            ex  = cx + math.sin(rad) * ln
            ey  = top + math.cos(rad) * ln
            c.create_line(cx, top, ex, ey, fill="#162030", width=wd)

        for ang, ln, wd in zip(angles_r, lengths, widths):
            rad = math.radians(ang)
            ex  = cx + math.sin(rad) * ln
            ey  = top + math.cos(rad) * ln
            c.create_line(cx, top, ex, ey, fill="#162030", width=wd)

        c.create_line(int(cw * 0.02), int(ch * 0.08), int(cw * 0.78), ch, fill="#162030", width=2)
        c.create_line(int(cw * 0.98), int(ch * 0.08), int(cw * 0.22), ch, fill="#162030", width=2)

    def _draw_scanlines(self, c, cw, ch):
        for y in range(0, ch, 6):
            c.create_rectangle(0, y+3, cw, y+4, fill="#000000", stipple="gray25", outline="")

    def _draw_fade(self, c, cw, ch):
        fade_h = int(ch * 0.12)
        for i in range(0, fade_h, 2):
            t = 1.0 - i / fade_h
            stip = "gray75" if t > 0.5 else "gray50"
            c.create_rectangle(0, i, cw, i+2, fill="#000000", stipple=stip, outline="")
        for i in range(0, fade_h, 2):
            t = i / fade_h
            stip = "gray75" if t < 0.5 else "gray50"
            c.create_rectangle(0, ch - fade_h + i, cw, ch - fade_h + i + 2,
                               fill="#000000", stipple=stip, outline="")

    def _draw_corner_web(self, c, ox, oy, sx, sy):
        size = 180
        col  = "#cc1111"
        angles = [0, 18, 36, 54, 72, 90]
        for ang in angles:
            rad = math.radians(ang)
            ex  = ox + sx * math.cos(rad) * size
            ey  = oy + sy * math.sin(rad) * size
            c.create_line(ox, oy, ex, ey, fill=col, width=1, stipple="gray25")

        for dist in [40, 80, 120, 160]:
            pts = []
            for ang in range(0, 95, 5):
                rad = math.radians(ang)
                px  = ox + sx * math.cos(rad) * dist
                py  = oy + sy * math.sin(rad) * dist
                pts.extend([px, py])
            if len(pts) >= 4:
                c.create_line(*pts, fill=col, width=1, stipple="gray25")

    def _draw_credits(self, c, cw, ch):
        cx    = cw // 2
        y_off = ch - self.scroll_y
        MAXW  = min(640, int(cw * 0.88))

        for item in self.credit_lines:
            h = self._item_height(item)
            if y_off > ch + 100 or y_off + h < -100:
                y_off += h
                continue

            k = item["kind"]
            if k == "spacer":
                y_off += item["h"]

            elif k == "spider_logo":
                self._draw_spider_logo(c, cx, y_off + 40)
                y_off += item["h"]

            elif k == "text":
                f    = item["font"]
                txt  = item["txt"]
                fill = item.get("fill", "#ffffff")
                if item.get("glow"):
                    shadow = item.get("shadow", "#880000")
                    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                        c.create_text(cx + dx, y_off + dy, text=txt, font=f,
                                      fill=shadow, anchor="n")
                c.create_text(cx, y_off, text=txt, font=f, fill=fill, anchor="n")
                y_off += f[1] + 14

            elif k == "divider_line":
                dw = min(180, MAXW // 3)
                c.create_line(cx - dw, y_off + 6, cx + dw, y_off + 6, fill=RED, width=2)
                c.create_line(cx - dw, y_off + 8, cx + dw, y_off + 8, fill=BLUE, width=1)
                y_off += 18

            elif k == "section_hdr":
                txt = item["txt"]
                sw  = 80
                c.create_line(cx - sw - 80, y_off + 10, cx - sw, y_off + 10, fill="#501010", width=1)
                c.create_line(cx + sw, y_off + 10, cx + sw + 80, y_off + 10, fill="#501010", width=1)
                c.create_text(cx, y_off, text=txt, font=("Courier", 9, "bold"),
                              fill="#c82828", anchor="n")
                y_off += 30

            elif k == "web_div":
                sym = item.get("symbol", "🕸")
                c.create_line(cx - 200, y_off + 10, cx - 18, y_off + 10, fill="#501515", width=1)
                c.create_line(cx + 18, y_off + 10, cx + 200, y_off + 10, fill="#501515", width=1)
                c.create_text(cx, y_off, text=sym, font=("Courier", 12), fill="#501515", anchor="n")
                y_off += 28

            elif k == "credit":
                role  = item["role"]
                name  = item["name"]
                small = item.get("small", False)
                nfont_sz = 18 if small else 24
                c.create_text(cx, y_off, text=role.upper(), font=("Courier", 9),
                              fill="#c84b4b", anchor="n")
                y_off += 16
                c.create_text(cx, y_off, text=name, font=("Courier", nfont_sz, "bold"),
                              fill="#f0e0e0", anchor="n")
                y_off += nfont_sz + 18

            elif k == "ty_box":
                y_off = self._draw_ty_box(c, cx, y_off, MAXW, item["text"])

    def _draw_ty_box(self, c, cx, y, maxw, text):
        lines   = text.split("\n")
        line_h  = 22
        total_h = len(lines) * line_h + 100
        box_x1  = cx - maxw // 2
        box_x2  = cx + maxw // 2

        c.create_rectangle(box_x1, y, box_x2, y + total_h,
                           fill="#000000", stipple="gray50", outline="#5c1414")
        c.create_text(box_x1 + 14, y + 12, text="🕷", font=("Courier", 13),
                      fill="#cc1111", anchor="nw")
        c.create_text(box_x2 - 14, y + 12, text="🕷", font=("Courier", 13),
                      fill="#cc1111", anchor="ne")

        c.create_text(cx, y + 18, text="THANK YOU FOR PLAYING",
                      font=("Courier", 14, "bold"), fill=RED2, anchor="n")

        ty = y + 52
        for line in lines:
            if line == "":
                ty += line_h // 2
                continue
            bold = line.startswith("Until") or line.startswith("From everyone")
            font = ("Courier", 11, "bold") if bold else ("Courier", 11)
            fill = "#ffffff" if bold else "#e6d2d2"
            c.create_text(cx, ty, text=line, font=font, fill=fill, anchor="n")
            ty += line_h

        ty += 16
        c.create_text(cx, ty, text="— POTATO PRODUCTIONS 🕷",
                      font=("Courier", 9), fill="#b41e1e", anchor="n")
        return y + total_h + 20

    def _item_height(self, item):
        k = item["kind"]
        if k == "spacer":       return item["h"]
        if k == "spider_logo":  return item["h"]
        if k == "text":         return item["font"][1] + 14
        if k == "divider_line": return 18
        if k == "section_hdr":  return 30
        if k == "web_div":      return 28
        if k == "credit":
            nfont_sz = 18 if item.get("small") else 24
            return 16 + nfont_sz + 18
        if k == "ty_box":
            lines = item["text"].split("\n")
            return len(lines) * 22 + 120
        return 0

    def _draw_spider_logo(self, c, cx, cy):
        col = "#cc1111"
        c.create_oval(cx-11, cy-14, cx+11, cy+14, fill=col, outline="")
        c.create_oval(cx-9,  cy-36, cx+9,  cy-18, fill=col, outline="")

        # Legs
        c.create_line(cx-11, cy-12, cx-35, cy-27, fill=col, width=2)
        c.create_line(cx-11, cy-5,  cx-36, cy-5,  fill=col, width=2)
        c.create_line(cx-11, cy+2,  cx-35, cy+16, fill=col, width=2)

        c.create_line(cx+11, cy-12, cx+35, cy-27, fill=col, width=2)
        c.create_line(cx+11, cy-5,  cx+36, cy-5,  fill=col, width=2)
        c.create_line(cx+11, cy+2,  cx+35, cy+16, fill=col, width=2)

        # Eyes
        c.create_oval(cx-8, cy-32, cx-2, cy-26, fill="#ffffff", outline="")
        c.create_oval(cx+2, cy-32, cx+8, cy-26, fill="#ffffff", outline="")

    @staticmethod
    def _alpha_color(hex_col, alpha):
        r = int(int(hex_col[1:3], 16) * alpha)
        g = int(int(hex_col[3:5], 16) * alpha)
        b = int(int(hex_col[5:7], 16) * alpha)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="▶  PLAY" if self.paused else "⏸  PAUSE")

def main():
    root = tk.Tk()
    root.geometry(f"{W}x{H}")
    app = CreditsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()