import tkinter as tk
from tkinter import ttk, colorchooser


def clamp(x, a, b):
    return min(b, max(a, x))


def rgb2hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = 60 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60 * ((b - r) / d + 2)
    else:
        h = 60 * ((r - g) / d + 4)
    s = 0.0 if mx == 0 else d / mx
    return h % 360, s, mx


def hsv2rgb(h, s, v):
    h %= 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    sector = int(h // 60)
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][sector]
    return (r + m) * 255, (g + m) * 255, (b + m) * 255


def rgb2cmyk(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k >= 1:
        return 0.0, 0.0, 0.0, 1.0
    return (1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k


def cmyk2rgb(c, m, y, k):
    return 255 * (1 - c) * (1 - k), 255 * (1 - m) * (1 - k), 255 * (1 - y) * (1 - k)


def to_hex(r, g, b):
    return "#%02x%02x%02x" % tuple(int(round(clamp(x, 0, 255))) for x in (r, g, b))


class ColorState:

    def __init__(self):
        self.r = self.g = self.b = 0.0
        self.h = self.s = self.v = 0.0
        self.c = self.m = self.y = self.k = 0.0

    def _update_hsv(self):
        h, s, v = rgb2hsv(self.r, self.g, self.b)
        self.s, self.v = s, v
        if s > 0 and v > 0:
            self.h = h

    def _update_cmyk(self):
        c, m, y, k = rgb2cmyk(self.r, self.g, self.b)
        self.k = k
        if k < 1:
            self.c, self.m, self.y = c, m, y

    def set_rgb(self, r, g, b):
        self.r, self.g, self.b = r, g, b
        self._update_hsv()
        self._update_cmyk()

    def set_hsv(self, h, s, v):
        self.h, self.s, self.v = h, s, v
        self.r, self.g, self.b = hsv2rgb(h, s, v)
        self._update_cmyk()

    def set_cmyk(self, c, m, y, k):
        self.c, self.m, self.y, self.k = c, m, y, k
        self.r, self.g, self.b = cmyk2rgb(c, m, y, k)
        self._update_hsv()

    def hex(self):
        return to_hex(self.r, self.g, self.b)


def lerp_stops(stops, t):
    n = len(stops) - 1
    pos = clamp(t, 0, 1) * n
    i = min(int(pos), n - 1)
    f = pos - i
    a, b = stops[i], stops[i + 1]
    return tuple(a[j] + (b[j] - a[j]) * f for j in range(3))


class GradientSlider(tk.Canvas):
    PAD = 9
    SEGMENTS = 40
    TRACK = "#d0d0d0"      # цвет однотонной дорожки в режиме plain

    def __init__(self, master, command, width=270, height=24, plain=False):
        super().__init__(master, width=width, height=height, highlightthickness=0)
        self.w, self.h = width, height
        self.command = command
        self.plain = plain
        self.frac = 0.0
        self.stops = [(0, 0, 0), (255, 255, 255)]
        x0, x1 = self.PAD, self.w - self.PAD
        seg = (x1 - x0) / self.SEGMENTS
        base = self.TRACK if plain else "#000"
        self.rects = [
            self.create_rectangle(x0 + i * seg, 7, x0 + (i + 1) * seg + 1, self.h - 7,
                                  fill=base, outline="")
            for i in range(self.SEGMENTS)
        ]
        self.create_rectangle(x0, 7, x1, self.h - 7, outline="#888")
        self.thumb = self.create_oval(0, 0, 0, 0, fill="white", outline="#222", width=2)
        self._colors = [None] * self.SEGMENTS
        self.bind("<Button-1>", self._on_mouse)
        self.bind("<B1-Motion>", self._on_mouse)

    def _on_mouse(self, e):
        f = clamp((e.x - self.PAD) / (self.w - 2 * self.PAD), 0, 1)
        self.frac = f
        self._move_thumb()
        self.command(f)

    def _move_thumb(self):
        x = self.PAD + self.frac * (self.w - 2 * self.PAD)
        self.coords(self.thumb, x - 8, self.h / 2 - 8, x + 8, self.h / 2 + 8)

    def update_slider(self, frac, stops):
        self.frac = clamp(frac, 0, 1)
        self.stops = stops
        self._move_thumb()
        if self.plain:
            return
        n = self.SEGMENTS
        for i in range(n):
            col = to_hex(*lerp_stops(stops, i / (n - 1)))
            if col != self._colors[i]:
                self._colors[i] = col
                self.itemconfigure(self.rects[i], fill=col)


RAINBOW = [hsv2rgb(h, 1, 1) for h in (0, 60, 120, 180, 240, 300, 360)]

MODELS = [
    ("rgb", "RGB", "красный, зелёный, синий (0-255)",
     [("r", "R", 255, 1, 0), ("g", "G", 255, 1, 0), ("b", "B", 255, 1, 0)]),
    ("cmyk", "CMYK", "голубой, пурпурный, жёлтый, чёрный (%)",
     [("c", "C", 100, 100, 1), ("m", "M", 100, 100, 1), ("y", "Y", 100, 100, 1), ("k", "K", 100, 100, 1)]),
    ("hsv", "HSV", "тон (°), насыщенность (%), яркость (%)",
     [("h", "H", 360, 1, 1), ("s", "S", 100, 100, 1), ("v", "V", 100, 100, 1)]),
]
SETTERS = {"rgb": "set_rgb", "cmyk": "set_cmyk", "hsv": "set_hsv"}
TORGB = {"rgb": lambda a: tuple(a), "cmyk": lambda a: cmyk2rgb(*a), "hsv": lambda a: hsv2rgb(*a)}

SV_W, SV_H = 300, 240
HEX = ["%02x" % i for i in range(256)]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Цветовые модели: CMYK - RGB - HSV")
        self.resizable(False, False)
        self.state_ = ColorState()
        self.state_.set_rgb(31, 94, 255)
        self.controls = {}
        self._palette_hue = None
        self._sharp_job = None
        self._render_pending = False
        self._skip = None
        self._build()
        self._render_now()

    def _build(self):
        left = ttk.Frame(self, padding=12)
        left.grid(row=0, column=0, sticky="n")
        right = ttk.Frame(self, padding=(0, 12, 12, 12))
        right.grid(row=0, column=1, sticky="n")

        self.swatch = tk.Canvas(left, width=SV_W, height=70, highlightthickness=1,
                                highlightbackground="#888")
        self.swatch.pack(pady=(0, 10))

        self.sv = tk.Canvas(left, width=SV_W, height=SV_H, highlightthickness=1,
                            highlightbackground="#888", cursor="crosshair")
        self.sv.pack()
        self.sv_img = tk.PhotoImage(width=SV_W, height=SV_H)
        self.sv.create_image(0, 0, image=self.sv_img, anchor="nw")
        self.marker = self.sv.create_oval(0, 0, 0, 0, outline="white", width=2)
        self.marker2 = self.sv.create_oval(0, 0, 0, 0, outline="black", width=1)
        self.sv.bind("<Button-1>", self._on_sv)
        self.sv.bind("<B1-Motion>", self._on_sv)

        self.hue_slider = GradientSlider(left, self._on_hue_slider, width=SV_W)
        self.hue_slider.pack(pady=(8, 0))

        hexrow = ttk.Frame(left)
        hexrow.pack(fill="x", pady=(10, 0))
        ttk.Label(hexrow, text="HEX").pack(side="left")
        self.hex_var = tk.StringVar()
        self.hex_entry = ttk.Entry(hexrow, textvariable=self.hex_var, width=9)
        self.hex_entry.pack(side="left", padx=8)
        self.hex_entry.bind("<KeyRelease>", self._on_hex)
        self.hex_entry.bind("<FocusOut>", lambda e: self.render())
        ttk.Button(hexrow, text="Палитра...", command=self._system_dialog).pack(side="right")

        for mid, title, hint, chans in MODELS:
            box = ttk.LabelFrame(right, text=f" {title}: {hint} ", padding=10)
            box.pack(fill="x", pady=(0, 10))
            for i, (attr, name, mx, scale, dec) in enumerate(chans):
                ttk.Label(box, text=name, width=3).grid(row=i, column=0, pady=3)
                sl = GradientSlider(box,
                                    lambda f, m=mid, a=attr: self._on_slider(m, a, f),
                                    width=270, height=24, plain=True)
                sl.grid(row=i, column=1, padx=6)
                var = tk.StringVar()
                ent = ttk.Entry(box, textvariable=var, width=7, justify="right")
                ent.grid(row=i, column=2)
                ent.bind("<KeyRelease>", lambda e, m=mid, a=attr: self._on_entry(m, a))
                ent.bind("<FocusOut>", lambda e: self.render())
                ent.bind("<Return>", lambda e: self.render())
                self.controls[(mid, attr)] = (sl, var, ent)

    def _chan(self, mid):
        return next(ch for m, _, _, ch in MODELS if m == mid)

    def _apply(self, mid, attr, internal_value):
        chans = self._chan(mid)
        vals = [getattr(self.state_, a) for a, *_ in chans]
        idx = [a for a, *_ in chans].index(attr)
        vals[idx] = internal_value
        getattr(self.state_, SETTERS[mid])(*vals)

    def _on_slider(self, mid, attr, frac):
        _, _, mx, scale, _ = next(c for c in self._chan(mid) if c[0] == attr)
        self._apply(mid, attr, frac * mx / scale)
        self.render()

    def _on_entry(self, mid, attr):
        _, var, ent = self.controls[(mid, attr)]
        _, _, mx, scale, _ = next(c for c in self._chan(mid) if c[0] == attr)
        try:
            val = float(var.get().replace(",", "."))
        except ValueError:
            return
        self._apply(mid, attr, clamp(val, 0, mx) / scale)
        self.render(skip=ent)

    def _on_sv(self, e):
        s = clamp(e.x / SV_W, 0, 1)
        v = 1 - clamp(e.y / SV_H, 0, 1)
        self.state_.set_hsv(self.state_.h, s, v)
        self.render()

    def _on_hue_slider(self, frac):
        self.state_.set_hsv(frac * 360, self.state_.s, self.state_.v)
        self.render()

    def _on_hex(self, _=None):
        t = self.hex_var.get().strip().lstrip("#")
        if len(t) != 6:
            return
        try:
            n = int(t, 16)
        except ValueError:
            return
        self.state_.set_rgb((n >> 16) & 255, (n >> 8) & 255, n & 255)
        self.render(skip=self.hex_entry)

    def _system_dialog(self):
        res = colorchooser.askcolor(color=self.state_.hex(), parent=self)
        if res and res[0]:
            self.state_.set_rgb(*res[0])
            self.render()

    def _build_sv(self, h, w, hh, zoom):
        r0, g0, b0 = hsv2rgb(h, 1, 1)
        small = tk.PhotoImage(width=w, height=hh)
        xs = [x / (w - 1) for x in range(w)]
        rows = []
        for y in range(hh):
            v = 1 - y / (hh - 1)
            rows.append("{" + " ".join(
                "#" + HEX[int(v * (255 - s * (255 - r0)) + .5)]
                + HEX[int(v * (255 - s * (255 - g0)) + .5)]
                + HEX[int(v * (255 - s * (255 - b0)) + .5)]
                for s in xs) + "}")
        small.put(" ".join(rows), to=(0, 0))
        self.sv_img.tk.call(self.sv_img, "copy", small, "-zoom", zoom, zoom)

    def _draw_sv(self):
        h = round(self.state_.h, 1)
        if self._palette_hue == h:
            return
        self._palette_hue = h
        self._build_sv(h, SV_W // 4, SV_H // 4, 4)
        if self._sharp_job:
            self.after_cancel(self._sharp_job)
        self._sharp_job = self.after(150, self._sharpen_sv)

    def _sharpen_sv(self):
        self._sharp_job = None
        self._build_sv(self._palette_hue, SV_W // 2, SV_H // 2, 2)

    def render(self, skip=None):
        self._skip = skip
        if not self._render_pending:
            self._render_pending = True
            self.after_idle(self._render_now)

    def _render_now(self):
        self._render_pending = False
        skip = self._skip
        st = self.state_
        self.swatch.configure(bg=st.hex())

        for mid, _, _, chans in MODELS:
            vals = [getattr(st, a) for a, *_ in chans]
            for i, (attr, name, mx, scale, dec) in enumerate(chans):
                sl, var, ent = self.controls[(mid, attr)]
                shown = vals[i] * scale
                sl.update_slider(shown / mx, None)
                if ent is not skip and self.focus_get() is not ent:
                    var.set(str(int(round(shown))) if dec == 0
                            else ("%.1f" % shown).rstrip("0").rstrip("."))

        if skip is not self.hex_entry and self.focus_get() is not self.hex_entry:
            self.hex_var.set(st.hex())

        self.hue_slider.update_slider(st.h / 360, RAINBOW)
        self._draw_sv()
        x, y = st.s * (SV_W - 1), (1 - st.v) * (SV_H - 1)
        self.sv.coords(self.marker, x - 7, y - 7, x + 7, y + 7)
        self.sv.coords(self.marker2, x - 8, y - 8, x + 8, y + 8)


if __name__ == "__main__":
    App().mainloop()