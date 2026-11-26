"""
Лабораторная работа 4. Алгоритмы отсечения отрезков (вариант 6).
  Часть 1: алгоритм средней точки (отсекающее окно - прямоугольник).
  Часть 2: отсечение отрезков выпуклым многоугольником (алгоритм Кируса-Бека).

Запуск:  python3 lab4_clipping.py     (только стандартная библиотека, tkinter)

Формат входных данных (часть 1):            Часть 2 (вместо последней строки - многоугольник):
  n                    - число отрезков        n
  X1 Y1 X2 Y2          - n строк               X1 Y1 X2 Y2 (n строк)
  Xmin Ymin Xmax Ymax  - окно                  m              - число вершин выпуклого многоугольника
                                               x y            - m строк (вершины по порядку обхода)
Текст между звёздочками (*...*) и после # считается комментарием.
"""
import math
import random
import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox

LEFT, RIGHT, BOTTOM, TOP = 1, 2, 4, 8


# ====================================================================== АЛГОРИТМЫ
def outcode(x, y, w):
    """4-битный код положения точки относительно окна w = (xmin, ymin, xmax, ymax)."""
    c = 0
    if x < w[0]:
        c |= LEFT
    elif x > w[2]:
        c |= RIGHT
    if y < w[1]:
        c |= BOTTOM
    elif y > w[3]:
        c |= TOP
    return c


def num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pt(p):
    return f"({num(p[0])}; {num(p[1])})"


def midpoint_clip(seg, w, eps=1e-3, max_log=150):
    """Алгоритм средней точки.
    Для отрезка: оба конца внутри окна - принять; оба в одной внешней полуплоскости (коды & != 0) - отбросить;
    иначе разделить пополам и повторить для обеих половин. Если длина части не больше eps, решение принимается
    по её середине. Видимая часть - от начала первой до конца последней принятой части."""
    a0, b0 = (seg[0], seg[1]), (seg[2], seg[3])
    acc, log = [], []
    stat = {"div": 0, "acc": 0, "rej": 0}

    def note(depth, text):
        if len(log) < max_log:
            log.append("  " * depth + text)
        elif len(log) == max_log:
            log.append("... (дальнейший протокол сокращён)")

    def rec(a, b, d):
        ca, cb = outcode(*a, w), outcode(*b, w)
        head = f"{pt(a)}–{pt(b)}  коды {ca:04b}/{cb:04b}: "
        if ca | cb == 0:
            acc.append((a, b))
            stat["acc"] += 1
            note(d, head + "оба конца в окне - принят")
            return
        if ca & cb:
            stat["rej"] += 1
            note(d, head + "оба конца по одну сторону - отброшен")
            return
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if math.hypot(b[0] - a[0], b[1] - a[1]) <= eps:
            if outcode(*m, w) == 0:
                acc.append((a, b))
                stat["acc"] += 1
                note(d, head + "длина ≤ ε, середина в окне - принят")
            else:
                stat["rej"] += 1
                note(d, head + "длина ≤ ε, середина вне окна - отброшен")
            return
        stat["div"] += 1
        note(d, head + f"делим в середине {pt(m)}")
        rec(a, m, d + 1)
        rec(m, b, d + 1)

    rec(a0, b0, 0)
    if not acc:
        status, vis = "не виден", None
    else:
        p, q = acc[0][0], acc[-1][1]
        vis = (p[0], p[1], q[0], q[1])
        full = abs(p[0] - a0[0]) + abs(p[1] - a0[1]) + abs(q[0] - b0[0]) + abs(q[1] - b0[1]) < 1e-9
        status = "полностью виден" if full else "частично виден"
    info = f"делений: {stat['div']}, принято частей: {stat['acc']}, отброшено: {stat['rej']}"
    return dict(status=status, vis=vis, info=info, log=log)


def cyrus_beck(seg, poly):
    """Отсечение отрезка выпуклым многоугольником (вершины против часовой стрелки).
    P(t) = P1 + t (P2 - P1), 0 <= t <= 1. Для каждого ребра с внутренней нормалью n:
        N = n·(P1 - Vi),  D = n·(P2 - P1),  t = -N / D.
    D > 0 - отрезок входит в полуплоскость (tE = max(tE, t)), D < 0 - выходит (tL = min(tL, t)).
    Если tE > tL - отрезок невидим."""
    x1, y1, x2, y2 = seg
    dx, dy = x2 - x1, y2 - y1
    te, tl = 0.0, 1.0
    log = [f"P(t) = ({num(x1)}; {num(y1)}) + t·({num(dx)}; {num(dy)}),  tE = 0, tL = 1"]
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        nx, ny = -(by - ay), (bx - ax)                       # внутренняя нормаль (обход против часовой)
        N = nx * (x1 - ax) + ny * (y1 - ay)
        D = nx * dx + ny * dy
        head = f"ребро {i + 1} {pt((ax, ay))}→{pt((bx, by))}, n=({num(nx)}; {num(ny)}), N={num(N)}, D={num(D)}: "
        if abs(D) < 1e-12:
            if N < 0:
                log.append(head + "отрезок параллелен ребру и лежит снаружи - невидим")
                return dict(status="не виден", vis=None, info="параллелен ребру снаружи", log=log, te=None, tl=None)
            log.append(head + "параллелен ребру, внутри полуплоскости - ребро не ограничивает")
            continue
        t = -N / D
        if D > 0:
            te = max(te, t)
            log.append(head + f"t = {num(t)} (вход), tE = {num(te)}")
        else:
            tl = min(tl, t)
            log.append(head + f"t = {num(t)} (выход), tL = {num(tl)}")
        if te > tl:
            log.append(f"tE = {num(te)} > tL = {num(tl)} - отрезок невидим")
            return dict(status="не виден", vis=None, info=f"tE={num(te)} > tL={num(tl)}", log=log, te=te, tl=tl)
    p = (x1 + te * dx, y1 + te * dy)
    q = (x1 + tl * dx, y1 + tl * dy)
    status = "полностью виден" if te == 0 and tl == 1 else "частично виден"
    log.append(f"Видимая часть: t от {num(te)} до {num(tl)}: {pt(p)}–{pt(q)}")
    return dict(status=status, vis=(p[0], p[1], q[0], q[1]), info=f"tE = {num(te)}, tL = {num(tl)}", log=log, te=te, tl=tl)


# ====================================================================== ДАННЫЕ
def parse(text, mode):
    """Разбор входного текста. Возвращает (отрезки, окно-прямоугольник или None, многоугольник)."""
    text = re.sub(r"\*[^*\n]*\*", " ", text)
    text = re.sub(r"#[^\n]*", " ", text)
    try:
        nums = [float(t.replace(",", ".")) for t in text.split()]
    except ValueError:
        raise ValueError("В данных есть нечисловое значение.")
    if not nums:
        raise ValueError("Данные пусты.")
    n = int(nums[0])
    if n < 0 or len(nums) < 1 + 4 * n + 4:
        raise ValueError("Не хватает данных: ожидаются n, n отрезков и окно.")
    segs = [tuple(nums[1 + 4 * i:5 + 4 * i]) for i in range(n)]
    rest = nums[1 + 4 * n:]
    window = None
    if len(rest) == 4:
        x0, y0, x1, y1 = rest
        if x0 >= x1 or y0 >= y1:
            raise ValueError("Окно задано неверно: нужно Xmin < Xmax и Ymin < Ymax.")
        window = (x0, y0, x1, y1)
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    else:
        m = int(rest[0])
        if m < 3 or len(rest) != 1 + 2 * m:
            raise ValueError("Многоугольник: ожидается m ≥ 3 и затем m строк x y.")
        poly = [(rest[1 + 2 * i], rest[2 + 2 * i]) for i in range(m)]
        poly = prepare_polygon(poly)
    if mode == 1 and window is None:
        raise ValueError("Для части 1 окно должно быть прямоугольником (Xmin Ymin Xmax Ymax).")
    return segs, window, poly


def prepare_polygon(poly):
    """Проверка выпуклости и приведение обхода к направлению против часовой стрелки."""
    n = len(poly)
    area2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    if abs(area2) < 1e-12:
        raise ValueError("Многоугольник вырожден (нулевая площадь).")
    if area2 < 0:
        poly = poly[::-1]
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1e-9:
            raise ValueError("Многоугольник не выпуклый.")
    return poly


SAMPLE_SEGS = [(3, 2, 8, 6), (-2, 3, 6, 9), (0, 0, 12, 4), (-3, -2, 1, 9), (12, 1, 14, 9),
               (-1, 5, 5, -1), (0, 8, 4, 10), (0, 2.5, 3.5, -1), (0, 4, 12, 4), (6, -2, 6, 9)]


def sample_text(mode):
    lines = [str(len(SAMPLE_SEGS))] + [" ".join(num(v) for v in s) for s in SAMPLE_SEGS]
    if mode == 1:
        lines.append("2 1 10 7")
    else:
        lines += ["6", "3 1", "8 1", "11 4", "8 7", "3 7", "1 4"]
    return "\n".join(lines) + "\n"


def random_text(mode):
    n = 8
    if mode == 1:
        x0, y0 = random.randint(-6, 0), random.randint(-5, 0)
        w, h = random.randint(5, 9), random.randint(4, 7)
        tail = [f"{x0} {y0} {x0 + w} {y0 + h}"]
        cx, cy = x0 + w / 2, y0 + h / 2
    else:
        while True:
            cx, cy, r = random.randint(-2, 2), random.randint(-2, 2), random.randint(4, 6)
            m = random.randint(5, 7)
            base = random.random() * 6.28
            ang = sorted(base + 6.2832 * (i + random.uniform(-.2, .2)) / m for i in range(m))
            pts = [(round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)) for a in ang]
            try:
                prepare_polygon(pts)
                break
            except ValueError:
                continue
        tail = [str(m)] + [f"{x} {y}" for x, y in pts]
    rnd = lambda: round(random.uniform(-11, 11), 1)
    segs = [f"{rnd()} {rnd()} {rnd()} {rnd()}" for _ in range(n)]
    return "\n".join([str(n)] + segs + tail) + "\n"


# ====================================================================== ИНТЕРФЕЙС
COL_WIN, COL_WIN_FILL, COL_SRC, COL_VIS, COL_SEL = "#1f5eff", "#e8efff", "#e08a00", "#1a9c3c", "#c2185b"


def nice_step(raw):
    mag = 10 ** math.floor(math.log10(raw))
    for k in (1, 2, 5, 10):
        if k * mag >= raw:
            return k * mag
    return 10 * mag


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа 4: отсечение отрезков")
        self.geometry("1350x860")
        self.minsize(1100, 700)
        avail = set(tkfont.families())
        fam = next((f for f in ("Ubuntu", "DejaVu Sans", "Noto Sans", "Segoe UI", "Arial") if f in avail), "TkDefaultFont")
        for nm in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            tkfont.nametofont(nm).configure(family=fam, size=10)
        self.mode = tk.IntVar(value=1)
        self.prev_mode = 1
        self.texts = {1: sample_text(1), 2: sample_text(2)}      # данные каждого режима хранятся отдельно
        self.eps = tk.StringVar(value="0.001")
        self.segs, self.poly, self.results, self.sel = [], [], [], None
        self.cx = self.cy = 0.0
        self.scale = 30.0
        self._drag = None
        self._build()
        self.load_sample()

    # ---------- построение окна
    def _build(self):
        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")
        ttk.Radiobutton(left, text="Часть 1: алгоритм средней точки\n(окно - прямоугольник)", value=1,
                        variable=self.mode, command=self.switch_mode).pack(anchor="w")
        ttk.Radiobutton(left, text="Часть 2: отсечение отрезков выпуклым\nмногоугольником (Кируса-Бека)", value=2,
                        variable=self.mode, command=self.switch_mode).pack(anchor="w", pady=(4, 0))
        row = ttk.Frame(left)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="Точность ε (часть 1):").pack(side="left")
        ttk.Entry(row, textvariable=self.eps, width=8).pack(side="left", padx=6)
        ttk.Label(left, text="Данные (формат из задания):").pack(anchor="w")
        self.text = tk.Text(left, width=34, height=22, font=("DejaVu Sans Mono", 10), undo=True)
        self.text.pack(fill="y")
        self.text.bind("<Control-Return>", lambda e: self.apply())
        for txt, cmd in (("Применить (Ctrl+Enter)", self.apply), ("Открыть файл...", self.open_file),
                         ("Сохранить файл...", self.save_file), ("Пример из задания", self.load_sample),
                         ("Случайный пример", self.load_random), ("Вписать в окно", self.fit)):
            ttk.Button(left, text=txt, command=cmd).pack(fill="x", pady=2)
        zr = ttk.Frame(left)
        zr.pack(fill="x", pady=2)
        ttk.Button(zr, text="Приблизить (+)", command=lambda: self.zoom_center(1.4)).pack(side="left", expand=True, fill="x")
        ttk.Button(zr, text="Отдалить (−)", command=lambda: self.zoom_center(1 / 1.4)).pack(side="left", expand=True, fill="x")
        self.status = ttk.Label(left, text="", wraplength=290, foreground="#b00020")
        self.status.pack(anchor="w", pady=6)

        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)
        self.cv = tk.Canvas(right, bg="white", highlightthickness=1, highlightbackground="#999")
        self.cv.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        self.cv.bind("<Configure>", lambda e: self.draw())
        self.cv.bind("<ButtonPress-1>", self._press)
        self.cv.bind("<B1-Motion>", self._move)
        self.cv.bind("<MouseWheel>", self._wheel)
        self.cv.bind("<Button-4>", lambda e: self._zoom(e, 1.15))
        self.cv.bind("<Button-5>", lambda e: self._zoom(e, 1 / 1.15))
        self.cv.bind("<Motion>", self._hover)
        self.bind("<plus>", lambda e: self.zoom_center(1.4))
        self.bind("<equal>", lambda e: self.zoom_center(1.4))
        self.bind("<minus>", lambda e: self.zoom_center(1 / 1.4))
        self.coord = ttk.Label(right, text="Колесо мыши - масштаб, перетаскивание - сдвиг")
        self.coord.pack(anchor="w", padx=8)

        bottom = ttk.Frame(right)
        bottom.pack(fill="x", padx=6, pady=6)
        cols = ("№", "Отрезок", "Статус", "Видимая часть", "Детали")
        self.tree = ttk.Treeview(bottom, columns=cols, show="headings", height=9)
        for c, wd in zip(cols, (40, 190, 120, 210, 220)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=wd, anchor="w")
        self.tree.pack(side="left", fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._select)
        sb = ttk.Scrollbar(bottom, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.log = tk.Text(bottom, width=60, height=11, font=("DejaVu Sans Mono", 9), wrap="none")
        self.log.pack(side="left", fill="both", expand=True, padx=(6, 0))

    # ---------- данные и расчёт
    def set_text(self, s):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", s)

    def switch_mode(self):
        """Переключение части 1 / части 2: сохраняем данные прежнего режима, показываем данные нового.
        Масштаб и сдвиг сетки при этом не меняются - меняется только картинка."""
        self.texts[self.prev_mode] = self.text.get("1.0", "end")
        self.prev_mode = self.mode.get()
        self.set_text(self.texts[self.prev_mode])
        self.apply(refit=False)

    def load_sample(self):
        self.set_text(sample_text(self.mode.get()))
        self.apply()

    def load_random(self):
        self.set_text(random_text(self.mode.get()))
        self.apply()

    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if p:
            with open(p, encoding="utf-8") as f:
                self.set_text(f.read())
            self.apply()

    def save_file(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end"))

    def apply(self, refit=True):
        mode = self.mode.get()
        try:
            segs, window, poly = parse(self.text.get("1.0", "end"), mode)
            eps = float(self.eps.get().replace(",", "."))
            if eps <= 0:
                raise ValueError("ε должно быть положительным.")
        except ValueError as e:
            self.status.config(text="Ошибка: " + str(e))
            return
        self.status.config(text="")
        self.segs, self.poly, self.sel = segs, poly, None
        if mode == 1:
            self.results = [midpoint_clip(s, window, eps) for s in segs]
        else:
            self.results = [cyrus_beck(s, poly) for s in segs]
        self.tree.delete(*self.tree.get_children())
        for i, (s, r) in enumerate(zip(segs, self.results), 1):
            self.tree.insert("", "end", iid=str(i - 1), values=(
                i, f"{pt(s[:2])}–{pt(s[2:])}", r["status"],
                "-" if r["vis"] is None else f"{pt(r['vis'][:2])}–{pt(r['vis'][2:])}", r["info"]))
        self.log.delete("1.0", "end")
        if refit:
            self.fit()
        else:
            self.draw()

    def _select(self, _e=None):
        s = self.tree.selection()
        self.sel = int(s[0]) if s else None
        self.log.delete("1.0", "end")
        if self.sel is not None:
            r = self.results[self.sel]
            self.log.insert("1.0", f"Отрезок {self.sel + 1}: {r['status']}\n" + "\n".join(r["log"]))
        self.draw()

    # ---------- вид (координаты <-> экран)
    def fit(self):
        W, H = max(self.cv.winfo_width(), 300), max(self.cv.winfo_height(), 200)
        xs = [p[0] for p in self.poly] + [s[0] for s in self.segs] + [s[2] for s in self.segs]
        ys = [p[1] for p in self.poly] + [s[1] for s in self.segs] + [s[3] for s in self.segs]
        if not xs:
            xs, ys = [-5, 5], [-5, 5]
        x0, x1, y0, y1 = min(xs + [0]), max(xs + [0]), min(ys + [0]), max(ys + [0])
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.scale = max(1e-3, min((W - 90) / max(x1 - x0, 1), (H - 70) / max(y1 - y0, 1)))
        self.draw()

    def zoom_center(self, k):
        """Приближение/отдаление относительно центра поля (для кнопок)."""
        self.scale = max(1e-3, min(1e6, self.scale * k))
        self.draw()

    def _press(self, e):
        self._drag = (e.x, e.y)

    def _move(self, e):
        if self._drag:
            self.cx -= (e.x - self._drag[0]) / self.scale
            self.cy += (e.y - self._drag[1]) / self.scale
            self._drag = (e.x, e.y)
            self.draw()

    def _wheel(self, e):
        self._zoom(e, 1.15 if e.delta > 0 else 1 / 1.15)

    def _zoom(self, e, k):
        W, H = self.cv.winfo_width(), self.cv.winfo_height()
        wx, wy = self.cx + (e.x - W / 2) / self.scale, self.cy - (e.y - H / 2) / self.scale
        self.scale = max(1e-3, min(1e6, self.scale * k))
        self.cx, self.cy = wx - (e.x - W / 2) / self.scale, wy + (e.y - H / 2) / self.scale
        self.draw()

    def _hover(self, e):
        W, H = self.cv.winfo_width(), self.cv.winfo_height()
        self.coord.config(text=f"x = {num(self.cx + (e.x - W / 2) / self.scale)},  "
                               f"y = {num(self.cy - (e.y - H / 2) / self.scale)}   "
                               f"(масштаб: {self.scale:.1f} пикс. на единицу)")

    # ---------- отрисовка
    def draw(self):
        cv = self.cv
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 50 or H < 50:
            return
        s, cx, cy = self.scale, self.cx, self.cy
        X = lambda x: W / 2 + (x - cx) * s
        Y = lambda y: H / 2 - (y - cy) * s
        xmin, xmax = cx - W / 2 / s, cx + W / 2 / s
        ymin, ymax = cy - H / 2 / s, cy + H / 2 / s
        st = nice_step(60 / s)
        k = math.ceil(xmin / st)
        while k * st <= xmax:                                           # вертикальные линии сетки и подписи
            cv.create_line(X(k * st), 0, X(k * st), H, fill="#e3e7ec")
            cv.create_text(X(k * st), H - 8, text=f"{k * st:g}", fill="#555", font=("TkDefaultFont", 8))
            k += 1
        k = math.ceil(ymin / st)
        while k * st <= ymax:                                           # горизонтальные
            cv.create_line(0, Y(k * st), W, Y(k * st), fill="#e3e7ec")
            cv.create_text(16, Y(k * st), text=f"{k * st:g}", fill="#555", font=("TkDefaultFont", 8))
            k += 1
        cv.create_line(X(0), 0, X(0), H, fill="#333", width=2)          # оси координат
        cv.create_line(0, Y(0), W, Y(0), fill="#333", width=2)
        cv.create_text(W - 12, max(12, min(H - 22, Y(0) - 10)), text="x", font=("TkDefaultFont", 11, "bold"))
        cv.create_text(max(10, min(W - 12, X(0) + 10)), 12, text="y", font=("TkDefaultFont", 11, "bold"))
        if self.poly:                                                   # отсекающее окно
            flat = [c for p in self.poly for c in (X(p[0]), Y(p[1]))]
            cv.create_polygon(*flat, fill=COL_WIN_FILL, outline=COL_WIN, width=3)
        for i, sg in enumerate(self.segs):                              # исходные отрезки
            hl = i == self.sel
            if hl:
                cv.create_line(X(sg[0]), Y(sg[1]), X(sg[2]), Y(sg[3]), fill=COL_SEL, width=7, stipple="gray25")
            cv.create_line(X(sg[0]), Y(sg[1]), X(sg[2]), Y(sg[3]), fill=COL_SRC, width=2, dash=(5, 3))
            for x, y in ((sg[0], sg[1]), (sg[2], sg[3])):
                cv.create_oval(X(x) - 3, Y(y) - 3, X(x) + 3, Y(y) + 3, fill=COL_SRC, outline="")
            cv.create_text(X((sg[0] + sg[2]) / 2) + 9, Y((sg[1] + sg[3]) / 2) - 9, text=str(i + 1),
                           fill=COL_SEL if hl else "#7a4b00", font=("TkDefaultFont", 9, "bold"))
        for r in self.results:                                          # видимые части
            if r["vis"]:
                v = r["vis"]
                cv.create_line(X(v[0]), Y(v[1]), X(v[2]), Y(v[3]), fill=COL_VIS, width=4)
                for x, y in ((v[0], v[1]), (v[2], v[3])):
                    cv.create_oval(X(x) - 4, Y(y) - 4, X(x) + 4, Y(y) + 4, fill=COL_VIS, outline="white")
        y0 = 14                                                         # легенда
        for col, txt in ((COL_WIN, "окно отсечения"), (COL_SRC, "исходные отрезки"), (COL_VIS, "видимые части")):
            cv.create_rectangle(10, y0 - 5, 28, y0 + 5, fill=col, outline="")
            cv.create_text(36, y0, text=txt, anchor="w", font=("TkDefaultFont", 9))
            y0 += 18


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        raise