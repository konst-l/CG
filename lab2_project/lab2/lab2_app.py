import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from PIL import Image, ImageTk

import image_ops as ops

PW, PH = 290, 220
HW, HH = 290, 84


def load_array(path):
    img = Image.open(path)
    img = img.convert("L") if img.mode in ("L", "1", "I;16", "I", "F") else img.convert("RGB")
    return np.array(img)


class Panel(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=4)
        self.title = ttk.Label(self, font=("TkDefaultFont", 10, "bold"))
        self.title.pack()
        self.pic = ttk.Label(self)
        self.pic.pack()
        self.hist = tk.Canvas(self, width=HW, height=HH, bg="white", highlightthickness=1,
                              highlightbackground="#999")
        self.hist.pack(pady=(4, 0))
        self.info = ttk.Label(self, justify="center", wraplength=PW + 20)
        self.info.pack()
        self._photo = None

    def show(self, title, arr, hist_arr=None, marks=(), info=""):
        self.title.config(text=title)
        im = Image.fromarray(arr)
        im.thumbnail((PW, PH), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(im)
        self.pic.config(image=self._photo)
        self.info.config(text=info)
        self._draw_hist(arr if hist_arr is None else hist_arr, marks)

    def _draw_hist(self, arr, marks):
        cv = self.hist
        cv.delete("all")
        if arr.ndim == 3:
            hs = [np.bincount(arr[..., c].ravel(), minlength=256) for c in range(3)]
            cols = ["#d33", "#2a2", "#33d"]
        else:
            hs, cols = [ops.histogram(arr)], ["#777"]
        top = max(1, max(h.max() for h in hs))
        base = HH - 14
        for h, col in zip(hs, cols):
            pts = []
            for i in range(256):
                x = i * (HW - 1) / 255
                y = base - np.sqrt(h[i] / top) * (base - 6)       # шкала sqrt, чтобы были видны «хвосты»
                if arr.ndim == 2:
                    cv.create_line(x, base, x, y, fill=col)
                pts += [x, y]
            if arr.ndim == 3:
                cv.create_line(*pts, fill=col)
        cv.create_line(0, base, HW, base, fill="#444")
        for v in (0, 128, 255):
            cv.create_text(min(max(v * (HW - 1) / 255, 8), HW - 10), HH - 6, text=str(v), font=("TkDefaultFont", 7))
        for t, col in marks:
            x = t * (HW - 1) / 255
            cv.create_line(x, 0, x, base, fill=col, width=2)


class App(tk.Tk):
    OTSU, TRI, MAN = "#d62728", "#1f5eff", "#2a9d3a"

    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа 2: контрастирование и глобальная пороговая обработка")
        self.img = self.img2 = self.mask = None
        self.last_result = None
        self.last_bins = {}
        self._job = None
        self.op_names = list(ops.POINT_OPS.values())
        self.op_keys = list(ops.POINT_OPS.keys())
        self._build()
        self._autoload()

    def _build(self):
        bar = ttk.Frame(self, padding=6)
        bar.pack(fill="x")
        for text, cmd in (("Открыть изображение...", self.open_main),
                          ("Второе изображение...", self.open_second),
                          ("Эталонная маска...", self.open_mask),
                          ("Сохранить результат...", self.save_result)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=3)
        self.status = ttk.Label(bar, text="Откройте изображение")
        self.status.pack(side="left", padx=12)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.nb = ttk.Notebook(body)
        self.nb.pack(side="left", fill="y", padx=6, pady=6)
        self.nb.bind("<<NotebookTabChanged>>", self.schedule)
        self.view = ttk.Frame(body)
        self.view.pack(side="left", fill="both", expand=True)
        self.panels = [Panel(self.view) for _ in range(4)]

        self._tab_point()
        self._tab_thresh()

    def _slider(self, parent, text, var, lo, hi, row, integer=False):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=2)
        val = ttk.Label(parent, width=6, anchor="e")
        val.grid(row=row, column=2)

        def upd(*_):
            v = var.get()
            val.config(text=str(int(round(v))) if integer else "%.2f" % v)
            self.schedule()

        s = ttk.Scale(parent, from_=lo, to=hi, variable=var, length=170, command=lambda _v: upd())
        s.grid(row=row, column=1, padx=4)
        upd()

    def _tab_point(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text="Операции + контраст")
        ttk.Label(f, text="Поэлементная операция", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w")
        self.op_var = tk.StringVar(value=self.op_names[0])
        cb = ttk.Combobox(f, textvariable=self.op_var, values=self.op_names, state="readonly", width=38)
        cb.grid(row=1, column=0, columnspan=3, pady=4)
        cb.bind("<<ComboboxSelected>>", self.schedule)
        self.c_var, self.k_var, self.g_var = tk.DoubleVar(value=0), tk.DoubleVar(value=1), tk.DoubleVar(value=1)
        self._slider(f, "c (сдвиг)", self.c_var, -255, 255, 2, integer=True)
        self._slider(f, "k (множитель)", self.k_var, 0.1, 5, 3)
        self._slider(f, "g (гамма)", self.g_var, 0.1, 5, 4)

        ttk.Separator(f).grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(f, text="Линейное контрастирование", font=("TkDefaultFont", 10, "bold")).grid(
            row=6, column=0, columnspan=3, sticky="w")
        self.cm_var = tk.StringVar(value="off")
        for i, (v, t) in enumerate((("off", "Выкл."), ("minmax", "По min / max"),
                                    ("percentile", "По процентилям"), ("manual", "Вручную [lo, hi]"))):
            ttk.Radiobutton(f, text=t, value=v, variable=self.cm_var, command=self.schedule).grid(
                row=7 + i, column=0, columnspan=3, sticky="w")
        self.pl_var, self.ph_var = tk.DoubleVar(value=1), tk.DoubleVar(value=99)
        self.lo_var, self.hi_var = tk.DoubleVar(value=0), tk.DoubleVar(value=255)
        self._slider(f, "процентиль нижний, %", self.pl_var, 0, 30, 11)
        self._slider(f, "процентиль верхний, %", self.ph_var, 70, 100, 12)
        self._slider(f, "lo", self.lo_var, 0, 254, 13, integer=True)
        self._slider(f, "hi", self.hi_var, 1, 255, 14, integer=True)

    def _tab_thresh(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text="Глобальный порог")
        ttk.Label(f, text="Какой объект выделяем", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.light_var = tk.BooleanVar(value=True)
        ttk.Radiobutton(f, text="Светлый объект на тёмном фоне", value=True,
                        variable=self.light_var, command=self.schedule).pack(anchor="w")
        ttk.Radiobutton(f, text="Тёмный объект на светлом фоне", value=False,
                        variable=self.light_var, command=self.schedule).pack(anchor="w")
        ttk.Separator(f).pack(fill="x", pady=8)
        ttk.Label(f, text="Методы: Оцу и треугольник.\nКрасная линия на гистограмме - Оцу,\n"
                          "синяя - треугольник, зелёная - ручной порог.",
                  justify="left").pack(anchor="w")
        ttk.Separator(f).pack(fill="x", pady=8)
        self.man_on = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Добавить ручной порог", variable=self.man_on, command=self.schedule).pack(anchor="w")
        self.man_var = tk.DoubleVar(value=128)
        row = ttk.Frame(f)
        row.pack(anchor="w")
        self._slider(row, "T", self.man_var, 0, 255, 0, integer=True)
        ttk.Separator(f).pack(fill="x", pady=8)
        ttk.Label(f, text="Если загружена эталонная маска,\nпоказываются IoU и F1 каждого метода.",
                  justify="left").pack(anchor="w")

    def _autoload(self):
        d = "test_images"
        if os.path.isdir(d):
            files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
            if files:
                self._set_main(os.path.join(d, files[0]))

    def _set_main(self, path):
        self.img = load_array(path)
        self.mask = None
        name = os.path.basename(path)
        mp = os.path.join(os.path.dirname(path), "masks", name[:-4] + "_mask.png")
        if os.path.exists(mp):
            self._set_mask(mp)
        self.status.config(text=f"{name}  {self.img.shape[1]}x{self.img.shape[0]}")
        self.schedule()

    def _set_mask(self, path):
        m = load_array(path)
        self.mask = m if m.ndim == 2 else ops.to_gray(m)

    def open_main(self):
        p = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if p:
            self._set_main(p)

    def open_second(self):
        p = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if p:
            self.img2 = load_array(p)
            self.schedule()

    def open_mask(self):
        p = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.bmp")])
        if p:
            self._set_mask(p)
            self.schedule()

    def save_result(self):
        if self.nb.index(self.nb.select()) == 0:
            if self.last_result is None:
                return
            p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if p:
                Image.fromarray(self.last_result).save(p)
        else:
            if not self.last_bins:
                return
            p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if p:
                base = p[:-4] if p.lower().endswith(".png") else p
                for key, arr in self.last_bins.items():
                    Image.fromarray(arr).save(f"{base}_{key}.png")

    def schedule(self, *_):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(25, self.update_view)

    def update_view(self):
        self._job = None
        if self.img is None:
            return
        for p in self.panels:
            p.grid_forget()
        if self.nb.index(self.nb.select()) == 0:
            self._update_point()
        else:
            self._update_thresh()

    def _other(self):
        """Второе изображение приводится к размеру и типу первого."""
        if self.img2 is None:
            return None
        im = Image.fromarray(self.img2).convert("L" if self.img.ndim == 2 else "RGB")
        return np.array(im.resize((self.img.shape[1], self.img.shape[0]), Image.BILINEAR))

    def _update_point(self):
        op = self.op_keys[self.op_names.index(self.op_var.get())]
        other = self._other()
        note = ""
        if op in ops.BINARY_OPS and other is None:
            note = "  (для этой операции откройте второе изображение)"
            op = "none"
        res = ops.pointwise(self.img, op, c=round(self.c_var.get()), k=self.k_var.get(),
                            gamma=self.g_var.get(), other=other)
        info_after = ""
        mode = self.cm_var.get()
        if mode != "off":
            res, lo, hi = ops.linear_contrast(res, mode, self.pl_var.get(), self.ph_var.get(),
                                              round(self.lo_var.get()), round(self.hi_var.get()))
            info_after = f"диапазон [{lo}, {hi}] -> [0, 255]"
        self.last_result = res

        def stat(a):
            g = ops.to_gray(a)
            return f"min={g.min()}  max={g.max()}  среднее={g.mean():.1f}  СКО={g.std():.1f}"

        self.panels[0].show("Исходное", self.img, info=stat(self.img))
        self.panels[1].show("Результат", res, info=stat(res) + ("\n" + info_after if info_after else ""))
        self.panels[0].grid(row=0, column=0, padx=4, pady=4)
        self.panels[1].grid(row=0, column=1, padx=4, pady=4)
        if note:
            self.status.config(text=self.status.cget("text").split("  (")[0] + note)

    def _update_thresh(self):
        gray = ops.to_gray(self.img)
        h = ops.histogram(gray)
        light = self.light_var.get()
        t_o, t_t = ops.otsu_threshold(h), ops.triangle_threshold(h)
        results = [("Метод Оцу", t_o, self.OTSU, "otsu"), ("Метод треугольника", t_t, self.TRI, "triangle")]
        if self.man_on.get():
            results.append(("Ручной порог", round(self.man_var.get()), self.MAN, "manual"))

        truth = None
        if self.mask is not None:
            truth = self.mask
            if truth.shape != gray.shape:
                truth = np.array(Image.fromarray(truth).resize((gray.shape[1], gray.shape[0]), Image.NEAREST))

        marks = [(t, col) for _, t, col, _ in results]
        self.panels[0].show("Исходное (яркость)", gray, marks=marks,
                            info=f"Оцу: T={t_o}    треугольник: T={t_t}")
        self.last_bins = {}
        for i, (name, t, col, key) in enumerate(results, start=1):
            b = ops.binarize(gray, t, light)
            self.last_bins[key] = b
            info = f"T = {t}"
            if truth is not None:
                iou, f1 = ops.iou_f1(b, truth)
                info += f"    IoU = {iou:.3f}    F1 = {f1:.3f}"
            self.panels[i].show(name, b, hist_arr=gray, marks=[(t, col)], info=info)
        for i in range(1 + len(results)):
            self.panels[i].grid(row=i // 3, column=i % 3, padx=4, pady=4)


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as e:      # на случай проблем с Tk / отсутствия библиотек
        messagebox.showerror("Ошибка", str(e))
        raise
