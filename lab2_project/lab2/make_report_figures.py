"""
Генерация иллюстраций для отчёта и таблицы результатов (без GUI).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import image_ops as ops

OUT = "report_figures"
TW, TH, HHIST = 240, 180, 70
POL = {"01": False, "03": False, "04": False, "05": False, "06": False, "08": False,
       "02": True, "09": True, "07": True}


def font(size):
    for f in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


F = font(12)


def load(path):
    return np.array(Image.open(path))


def hist_img(arr, marks=()):
    im = Image.new("RGB", (TW, HHIST), "white")
    d = ImageDraw.Draw(im)
    if arr.ndim == 3:
        hs, cols = [np.bincount(arr[..., c].ravel(), minlength=256) for c in range(3)], ["#d33", "#2a2", "#33d"]
    else:
        hs, cols = [ops.histogram(arr)], ["#777"]
    top = max(1, max(h.max() for h in hs))
    base = HHIST - 12
    for h, col in zip(hs, cols):
        pts = [(i * (TW - 1) / 255, base - np.sqrt(h[i] / top) * (base - 4)) for i in range(256)]
        if arr.ndim == 3:
            d.line(pts, fill=col)
        else:
            for x, y in pts:
                d.line([(x, base), (x, y)], fill=col)
    d.line([(0, base), (TW, base)], fill="#444")
    for v in (0, 128, 255):
        d.text((min(max(v * (TW - 1) / 255 - 6, 0), TW - 20), base + 1), str(v), fill="black", font=font(9))
    for t, col in marks:
        x = t * (TW - 1) / 255
        d.line([(x, 0), (x, base)], fill=col, width=2)
    return im


def tile(arr, title, sub="", hist=None, marks=()):
    im = Image.fromarray(arr).convert("RGB")
    im.thumbnail((TW, TH))
    t = Image.new("RGB", (TW, 20 + TH + HHIST + 18), "white")
    d = ImageDraw.Draw(t)
    d.text((2, 2), title, fill="black", font=F)
    t.paste(im, (0, 20))
    t.paste(hist_img(arr if hist is None else hist, marks), (0, 20 + TH))
    d.text((2, 20 + TH + HHIST + 2), sub, fill="#333", font=font(11))
    return t


def sheet(tiles, cols, path):
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    w = cols * (TW + 8) + 8
    h = sum(r[0].height + 8 for r in rows) + 8
    s = Image.new("RGB", (w, h), "white")
    y = 8
    for r in rows:
        for j, t in enumerate(r):
            s.paste(t, (8 + j * (TW + 8), y))
        y += r[0].height + 8
    s.save(path)


def stat(a):
    g = ops.to_gray(a)
    return f"min={g.min()} max={g.max()} mean={g.mean():.0f} std={g.std():.0f}"


def main():
    os.makedirs(OUT, exist_ok=True)
    lines = []
    d = "test_images"

    # 1. глобальная пороговая обработка
    lines.append("GLOBAL THRESHOLDING: image, polarity, T_otsu, IoU_otsu, F1_otsu, T_triangle, IoU_tri, F1_tri")
    for name in sorted(f[:-4] for f in os.listdir(d) if f.endswith(".png")):
        k = name[:2]
        if k not in POL:
            continue
        g = ops.to_gray(load(f"{d}/{name}.png"))
        gt = load(f"{d}/masks/{name}_mask.png")
        h = ops.histogram(g)
        to, tt = ops.otsu_threshold(h), ops.triangle_threshold(h)
        bo, bt = ops.binarize(g, to, POL[k]), ops.binarize(g, tt, POL[k])
        (io, fo), (it, ft) = ops.iou_f1(bo, gt), ops.iou_f1(bt, gt)
        lines.append(f"{name}: {'light' if POL[k] else 'dark'} | {to} | {io:.3f} | {fo:.3f} | {tt} | {it:.3f} | {ft:.3f}")
        sheet([tile(g, "Original", stat(g), marks=[(to, "#d62728"), (tt, "#1f5eff")]),
               tile(bo, "Otsu", f"T={to} IoU={io:.3f}", hist=g, marks=[(to, "#d62728")]),
               tile(bt, "Triangle", f"T={tt} IoU={it:.3f}", hist=g, marks=[(tt, "#1f5eff")]),
               tile(gt, "Ground truth", "")], 4, f"{OUT}/thr_{name}.png")

    # 2. линейное контрастирование
    lines.append("")
    lines.append("LINEAR CONTRAST: image, mode, lo, hi, std_before, std_after")
    for name in ("05_low_contrast", "07_underexposed", "08_overexposed", "10_color_low_contrast"):
        a = load(f"{d}/{name}.png")
        t = [tile(a, "Original", stat(a))]
        for mode, kw in (("minmax", {}), ("percentile", {"p_low": 1, "p_high": 99}),
                         ("manual", {"lo": int(np.percentile(a, 2)), "hi": int(np.percentile(a, 98))})):
            r, lo, hi = ops.linear_contrast(a, mode, **kw)
            t.append(tile(r, f"Linear: {mode}", f"[{lo},{hi}] " + stat(r)))
            lines.append(f"{name} | {mode} | {lo} | {hi} | {ops.to_gray(a).std():.1f} | {ops.to_gray(r).std():.1f}")
        sheet(t, 4, f"{OUT}/contrast_{name}.png")

    # 3. поэлементные операции над одним изображением и над двумя
    a = load(f"{d}/07_underexposed.png")
    ops_list = [("none", {}, "Original"), ("add", {"c": 60}, "I + 60"), ("mul", {"k": 3}, "I * 3"),
                ("gamma", {"gamma": 0.45}, "gamma = 0.45"), ("log", {}, "log"), ("neg", {}, "negative")]
    sheet([tile(ops.pointwise(a, op, **kw), title, stat(ops.pointwise(a, op, **kw))) for op, kw, title in ops_list],
          3, f"{OUT}/pointwise_single.png")

    A = load(f"{d}/01_bimodal_dark_objects.png")
    B = load(f"{d}/11_gradient_for_binary_ops.png")
    bin_list = [("sum", "A + B"), ("diff", "|A - B|"), ("prod", "A * B / 255"),
                ("mean", "(A + B) / 2"), ("max", "max(A, B)"), ("min", "min(A, B)")]
    sheet([tile(A, "A"), tile(B, "B (gradient)")] +
          [tile(ops.pointwise(A, op, other=B), title) for op, title in bin_list], 4, f"{OUT}/pointwise_binary.png")

    open(f"{OUT}/results.txt", "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
