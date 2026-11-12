import math
import time
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

def rnd(v):
    return math.floor(v + 0.5)


# ============================================================ АЛГОРИТМЫ
# Каждый возвращает словарь: P - список пикселей (x, y[, яркость]), T - строки таблицы шагов,
# H - заголовки таблицы, info - пояснение с числами. rec=False отключает запись таблицы (для замера времени).

def stepwise(x1, y1, x2, y2, rec=True):
    """Пошаговый алгоритм: y = k*x + b, для каждого целого x вычисляем y и округляем."""
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return dict(P=[(x1, y1)], T=[(x1, y1)], H=["x", "y"], info="Отрезок вырожден в точку.")
    sw = abs(dy) > abs(dx)                       # ведущая ось: y, если отрезок «крутой»
    a1, a2 = (y1, y2) if sw else (x1, x2)
    k = dx / dy if sw else dy / dx
    b = (x1 if sw else y1) - k * a1
    s = 1 if a2 > a1 else -1
    P, T = [], []
    for a in range(a1, a2 + s, s):
        v = k * a + b
        r = rnd(v)
        P.append((r, a) if sw else (a, r))
        if rec:
            T.append((a, f"{v:.3f}", r))
    H = ["y", "x = k·y + b", "round(x)"] if sw else ["x", "y = k·x + b", "round(y)"]
    info = (f"Ведущая ось - {'y' if sw else 'x'}; k = {'Δx/Δy' if sw else 'Δy/Δx'} = "
            f"{dx if sw else dy}/{dy if sw else dx} = {k:.4f}; b = {b:.4f}")
    return dict(P=P, T=T, H=H, info=info)


def dda(x1, y1, x2, y2, rec=True):
    """ЦДА: L = max(|dx|,|dy|) шагов, на каждом к x и y прибавляем dx/L и dy/L."""
    dx, dy = x2 - x1, y2 - y1
    L = max(abs(dx), abs(dy))
    H = ["i", "x", "y", "round x", "round y"]
    if L == 0:
        return dict(P=[(x1, y1)], T=[(0, x1, y1, x1, y1)], H=H, info="Отрезок вырожден в точку.")
    sx, sy = dx / L, dy / L
    x, y = float(x1), float(y1)
    P, T = [], []
    for i in range(L + 1):
        p, q = rnd(x), rnd(y)
        P.append((p, q))
        if rec:
            T.append((i, f"{x:.3f}", f"{y:.3f}", p, q))
        x += sx
        y += sy
    return dict(P=P, T=T, H=H, info=f"L = max(|Δx|, |Δy|) = {L}; шаги: Δx/L = {sx:.4f}, Δy/L = {sy:.4f}")


def bres(x1, y1, x2, y2, rec=True):
    """Брезенхем для отрезка (все октанты), только целые числа."""
    dx, dy = abs(x2 - x1), -abs(y2 - y1)
    sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
    e, x, y = dx + dy, x1, y1
    P, T = [], []
    while True:
        e2 = 2 * e
        P.append((x, y))
        if rec:
            T.append((len(P) - 1, x, y, e, e2))
        if x == x2 and y == y2:
            break
        if e2 >= dy:
            e += dy
            x += sx
        if e2 <= dx:
            e += dx
            y += sy
    info = (f"|Δx| = {dx}, |Δy| = {-dy}; e₀ = |Δx| - |Δy| = {dx + dy}; если 2e ≥ -|Δy| - шаг по x "
            f"(e += -|Δy|); если 2e ≤ |Δx| - шаг по y (e += |Δx|)")
    return dict(P=P, T=T, H=["i", "x", "y", "ошибка e", "2e"], info=info)


def circ(cx, cy, r, _=0, rec=True):
    """Брезенхем для окружности: считаем 1/8 дуги, остальные 7 точек - по симметрии."""
    x, y, d = 0, r, 3 - 2 * r
    P, T = [], []
    while x <= y:
        if rec:
            T.append((x, y, d))
        for p, q in ((x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)):
            P.append((cx + p, cy + q))
        if d > 0:
            d += 4 * (x - y) + 10
            y -= 1
        else:
            d += 4 * x + 6
        x += 1
    info = (f"Считается 1/8 окружности (от x = 0 до x = y), остальные точки - по симметрии. d₀ = 3 - 2R = {3 - 2 * r}; "
            f"если d > 0: y--, d += 4(x - y) + 10, иначе d += 4x + 6")
    return dict(P=P, T=T, H=["x", "y", "d"], info=info)


def wu(x1, y1, x2, y2, rec=True):
    """Сглаживание Ву: на каждом шаге закрашиваются две клетки с яркостью 1-f и f."""
    P, T = [], []
    steep = abs(y2 - y1) > abs(x2 - x1)
    if steep:
        x1, y1, x2, y2 = y1, x1, y2, x2
    if x1 > x2:
        x1, x2, y1, y2 = x2, x1, y2, y1
    g = 0 if x2 == x1 else (y2 - y1) / (x2 - x1)
    y = float(y1)
    for x in range(x1, x2 + 1):
        yi = math.floor(y)
        f = y - yi
        for yy, a in ((yi, 1 - f), (yi + 1, f)):
            if a > 0.004:
                P.append((yy, x, a) if steep else (x, yy, a))
        if rec:
            T.append((x, f"{y:.3f}", f"{f:.3f}", f"{1 - f:.3f}", f"{f:.3f}"))
        y += g
    return dict(P=P, T=T, H=["ведущая коорд.", "вторая (точная)", "дробная часть f", "яркость 1-f", "яркость f"],
                info="Алгоритм Ву: на каждом шаге по ведущей оси закрашиваются две соседние клетки "
                     "с яркостью 1 - f и f, где f - дробная часть точной координаты.")


ALG = {"stepwise": stepwise, "dda": dda, "bres": bres, "circ": circ, "wu": wu}
NAMES = [("stepwise", "Пошаговый"), ("dda", "ЦДА"), ("bres", "Брезенхем (отрезок)"),
         ("circ", "Брезенхем (окружность)"), ("wu", "Сглаживание Ву (доп.)")]

EXPLAIN = (
    "Растр - это набор клеток (пикселей). Целая точка (x, y) - это ЦЕНТР клетки: клетка занимает квадрат\n"
    "[x - 1/2; x + 1/2] x [y - 1/2; y + 1/2]. Поэтому линии сетки проходят через полуцелые значения\n"
    "(..., -1/2, 1/2, 1 1/2, ...), а подписи на осях стоят строго по центрам клеток.\n\n"
    "Ось X проходит через центры клеток с y = 0, ось Y - через центры клеток с x = 0.\n"
    "Ось Y направлена вверх (как в математике, а не как на экране).\n\n"
    "Красная линия - идеальный отрезок или окружность в непрерывной плоскости.\n"
    "Алгоритм выбирает для неё ближайшие клетки (синие).")

PIX, GRID, AXIS, IDEAL = "#1f5eff", "#dde3e9", "#3a4452", "#d62728"


def blend(a):
    """Смешивание цвета пикселя с белым фоном по яркости a (для сглаживания)."""
    c = [int(PIX[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(255 + (v - 255) * a) for v in c)


# ============================================================ ИНТЕРФЕЙС
class App(tk.Tk):
    def __init__(self):
        super().__init__()
                # единый шрифт для всего приложения
        available = set(tkfont.families())
        family = next((f for f in ("Arial")
                       if f in available), "TkDefaultFont")
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            tkfont.nametofont(name).configure(family=family, size=10)
        self.title("Лабораторная работа 3: базовые растровые алгоритмы")
        self.geometry("1250x850")
        self.minsize(1000, 680)
        self.res = dict(P=[], T=[], H=[], info="")
        self.cx = self.cy = 0.0
        self.ideal = None
        self.alg = tk.StringVar(value="stepwise")
        self.vals = [tk.StringVar(value=v) for v in ("-5", "-3", "10", "6")]
        self._build()
        self.after(150, self.build)          # после того как окно отобразилось и известен размер холста

    def _build(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side="left", fill="y")
        for key, name in NAMES:
            ttk.Radiobutton(left, text=name, value=key, variable=self.alg, command=self.on_alg).pack(anchor="w")
        ttk.Separator(left).pack(fill="x", pady=8)
        self.labels, self.entries = [], []
        grid = ttk.Frame(left)
        grid.pack(fill="x")
        for i in range(4):
            lb = ttk.Label(grid, text="")
            lb.grid(row=i, column=0, sticky="w", pady=2)
            en = ttk.Entry(grid, textvariable=self.vals[i], width=8)
            en.grid(row=i, column=1, padx=6)
            en.bind("<Return>", lambda e: self.build())
            self.labels.append(lb)
            self.entries.append(en)
        ttk.Button(left, text="Построить", command=self.build).pack(fill="x", pady=10)
        ttk.Label(left, text="Масштаб (пикселей на клетку)").pack(anchor="w")
        self.zoom = tk.Scale(left, from_=4, to=60, orient="horizontal", command=lambda _v: self.draw())
        self.zoom.set(24)
        self.zoom.pack(fill="x")
        self.sn = ttk.Label(left, text="Показано пикселей:")
        self.sn.pack(anchor="w", pady=(8, 0))
        self.shown = tk.Scale(left, from_=0, to=1, orient="horizontal", command=lambda _v: self.draw())
        self.shown.pack(fill="x")
        ttk.Label(left, text="Синие клетки - пиксели,\nкрасная линия - идеальная,\nчёрные линии - оси координат.",
                  foreground="#555").pack(anchor="w", pady=14)

        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)
        self.cv = tk.Canvas(right, bg="white", highlightthickness=1, highlightbackground="#999")
        self.cv.pack(fill="both", expand=True, padx=6, pady=6)
        self.cv.bind("<Configure>", lambda e: self.draw())

        nb = ttk.Notebook(right)
        nb.pack(fill="x", padx=6, pady=(0, 6))
        t1 = ttk.Frame(nb)
        nb.add(t1, text="Вычисления")
        self.info = ttk.Label(t1, wraplength=900, justify="left")
        self.info.pack(anchor="w", padx=6, pady=4)
        self.tree = self._table(t1, 7)
        t2 = ttk.Frame(nb)
        nb.add(t2, text="Замер времени")
        top = ttk.Frame(t2)
        top.pack(fill="x", padx=6, pady=4)
        ttk.Button(top, text="Запустить замер", command=self.run_bench).pack(side="left")
        self.bstat = ttk.Label(top, text="  Среднее время одного вызова без отрисовки и без записи таблицы.")
        self.bstat.pack(side="left")
        self.btree = self._table(t2, 7, cols=("Алгоритм", "Тест", "Пикселей", "мкс на вызов", "нс на пиксель"))
        t3 = ttk.Frame(nb)
        nb.add(t3, text="Привязка координат к сетке")
        ttk.Label(t3, text=EXPLAIN, justify="left").pack(anchor="w", padx=8, pady=8)

    def _table(self, parent, height, cols=()):
        fr = ttk.Frame(parent)
        fr.pack(fill="x", padx=6, pady=(0, 6))
        tr = ttk.Treeview(fr, columns=cols, show="headings", height=height)
        sb = ttk.Scrollbar(fr, orient="vertical", command=tr.yview)
        tr.configure(yscrollcommand=sb.set)
        tr.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")
        for c in cols:
            tr.heading(c, text=c)
            tr.column(c, width=130, anchor="e")
        return tr

    # ---------- данные
    def on_alg(self):
        c = self.alg.get() == "circ"
        names = ["x₀ (центр)", "y₀ (центр)", "R", ""] if c else ["x₁", "y₁", "x₂", "y₂"]
        for i in range(4):
            self.labels[i].config(text=names[i])
        if c:
            self.entries[3].grid_remove()
            self.labels[3].grid_remove()
        else:
            self.entries[3].grid()
            self.labels[3].grid()
        self.build()

    def args(self):
        v = []
        for s in self.vals:
            try:
                v.append(max(-3000, min(3000, int(float(s.get())))))
            except ValueError:
                v.append(0)
        if self.alg.get() == "circ":
            v[2] = max(1, v[2])
        return v

    def build(self):
        if not self.labels[0].cget("text"):
            self.on_alg()
            return
        v = self.args()
        a = self.alg.get()
        self.res = ALG[a](v[0], v[1], v[2], v[3], True)
        self.ideal = ("c", v[0], v[1], v[2]) if a == "circ" else ("l", v[0], v[1], v[2], v[3])
        xs = [p[0] for p in self.res["P"]]
        ys = [p[1] for p in self.res["P"]]
        x0, x9, y0, y9 = min(xs), max(xs), min(ys), max(ys)
        self.cx, self.cy = (x0 + x9) / 2, (y0 + y9) / 2
        W, H = max(self.cv.winfo_width(), 300), max(self.cv.winfo_height(), 200)
        self.zoom.set(max(4, min(60, int(min((W - 70) / (x9 - x0 + 3), (H - 50) / (y9 - y0 + 3))))))
        n = len(self.res["P"])
        self.shown.config(to=max(1, n))
        self.shown.set(n)
        self.fill_table()
        self.draw()

    def fill_table(self):
        tr = self.tree
        tr.delete(*tr.get_children())
        cols = self.res["H"]
        tr["columns"] = cols
        for c in cols:
            tr.heading(c, text=c)
            tr.column(c, width=140, anchor="e")
        for row in self.res["T"][:500]:
            tr.insert("", "end", values=row)
        uniq = len({(p[0], p[1]) for p in self.res["P"]})
        extra = "  Показаны первые 500 строк." if len(self.res["T"]) > 500 else ""
        self.info.config(text=f"{self.res['info']} Всего пикселей: {uniq}.{extra}")

    # ---------- отрисовка
    def draw(self):
        cv = self.cv
        cv.delete("all")
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 50 or H < 50:
            return
        s = float(self.zoom.get())
        cx, cy = self.cx, self.cy
        X = lambda i: W / 2 + (i - cx) * s
        Y = lambda j: H / 2 - (j - cy) * s
        i0, i1 = math.floor(cx - W / 2 / s) - 1, math.ceil(cx + W / 2 / s) + 1
        j0, j1 = math.floor(cy - H / 2 / s) - 1, math.ceil(cy + H / 2 / s) + 1
        P = self.res["P"]
        n = int(self.shown.get())
        self.sn.config(text=f"Показано пикселей: {n} / {len(P)}")
        for p in P[:n]:
            a = p[2] if len(p) > 2 else 1
            cv.create_rectangle(X(p[0] - .5), Y(p[1] + .5), X(p[0] + .5), Y(p[1] - .5),
                                fill=blend(a), outline="")
        if 0 < n <= len(P):                                      # последний выставленный пиксель обводим
            x, y = P[n - 1][0], P[n - 1][1]
            cv.create_rectangle(X(x - .5), Y(y + .5), X(x + .5), Y(y - .5), outline="black", width=2)
        if s >= 6:                                               # линии сетки - по полуцелым значениям
            for i in range(i0, i1 + 1):
                cv.create_line(X(i + .5), 0, X(i + .5), H, fill=GRID)
            for j in range(j0, j1 + 1):
                cv.create_line(0, Y(j + .5), W, Y(j + .5), fill=GRID)
        cv.create_line(X(0), 0, X(0), H, fill=AXIS, width=2)
        cv.create_line(0, Y(0), W, Y(0), fill=AXIS, width=2)
        if self.ideal:
            if self.ideal[0] == "c":
                _, x, y, r = self.ideal
                cv.create_oval(X(x - r), Y(y + r), X(x + r), Y(y - r), outline=IDEAL, width=2)
            else:
                _, x1, y1, x2, y2 = self.ideal
                cv.create_line(X(x1), Y(y1), X(x2), Y(y2), fill=IDEAL, width=2)
        st = max(1, math.ceil(34 / s))
        for i in range(i0, i1 + 1):
            if i % st == 0:
                cv.create_text(X(i), H - 8, text=str(i), fill="#555", font=("TkDefaultFont", 8))
        for j in range(j0, j1 + 1):
            if j % st == 0:
                cv.create_text(14, Y(j), text=str(j), fill="#555", font=("TkDefaultFont", 8))
        cv.create_text(W - 14, max(14, min(H - 24, Y(0) - 10)), text="x", font=("TkDefaultFont", 11, "bold"))
        cv.create_text(max(10, min(W - 14, X(0) + 10)), 14, text="y", font=("TkDefaultFont", 11, "bold"))

    # ---------- замер времени
    def run_bench(self):
        self.bstat.config(text="  Идёт замер...")
        self.update_idletasks()
        self.after(30, self._bench)

    def _bench(self):
        tr = self.btree
        tr.delete(*tr.get_children())
        tests = [(f, nm, a) for f, nm in (("stepwise", "Пошаговый"), ("dda", "ЦДА"),
                                          ("bres", "Брезенхем"), ("wu", "Ву"))
                 for a in ((0, 0, 1000, 600), (0, 0, 20, 13))]
        tests += [("circ", "Брезенхем (окружность)", (0, 0, 300, 0)), ("circ", "Брезенхем (окружность)", (0, 0, 20, 0))]
        for key, nm, a in tests:
            fn = ALG[key]
            px = len({(p[0], p[1]) for p in fn(*a, False)["P"]})
            for _ in range(30):
                fn(*a, False)
            n, t0 = 0, time.perf_counter()
            while True:
                for _ in range(20):
                    fn(*a, False)
                n += 20
                t = time.perf_counter() - t0
                if t >= 0.12:
                    break
            us = t * 1e6 / n
            test = f"R = {a[2]}" if key == "circ" else f"({a[0]},{a[1]})-({a[2]},{a[3]})"
            tr.insert("", "end", values=(nm, test, px, f"{us:.2f}", f"{us * 1000 / px:.1f}"))
        self.bstat.config(text="  Готово. Результат зависит от компьютера; запустите 3-5 раз.")


if __name__ == "__main__":
    App().mainloop()