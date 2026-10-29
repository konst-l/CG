import numpy as np


# вспомогательное
def to_gray(img):
    """RGB -> яркость по формуле ITU-R BT.601: Y = 0.299 R + 0.587 G + 0.114 B."""
    if img.ndim == 2:
        return img
    y = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
    return np.clip(np.rint(y), 0, 255).astype(np.uint8)


def histogram(gray):
    """Гистограмма: число пикселей каждого уровня яркости 0..255."""
    return np.bincount(gray.ravel(), minlength=256)


def _to_uint8(x):
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


# поэлементные операции
POINT_OPS = {
    "none": "Без операции",
    "add": "Сложение с константой: I + c",
    "mul": "Умножение на константу: I * k",
    "neg": "Негатив: 255 - I",
    "gamma": "Гамма-коррекция: 255 * (I/255)^g",
    "log": "Логарифмическое преобразование",
    "sum": "Сумма двух изображений: A + B",
    "diff": "Модуль разности: |A - B|",
    "prod": "Произведение: A * B / 255",
    "mean": "Среднее: (A + B) / 2",
    "max": "Максимум: max(A, B)",
    "min": "Минимум: min(A, B)",
}
BINARY_OPS = {"sum", "diff", "prod", "mean", "max", "min"}


def pointwise(img, op, c=0.0, k=1.0, gamma=1.0, other=None):
    """Поэлементная операция. Каждый выходной пиксель зависит только от
    соответствующего пикселя (или пары пикселей двух изображений)."""
    a = img.astype(np.float64)
    if op == "none":
        return img.copy()
    if op == "add":
        r = a + c
    elif op == "mul":
        r = a * k
    elif op == "neg":
        r = 255.0 - a
    elif op == "gamma":
        r = 255.0 * (a / 255.0) ** gamma
    elif op == "log":
        r = 255.0 / np.log(256.0) * np.log1p(a)
    elif op in BINARY_OPS:
        if other is None:
            raise ValueError("Для этой операции нужно второе изображение")
        b = other.astype(np.float64)
        r = {"sum": a + b, "diff": np.abs(a - b), "prod": a * b / 255.0,
             "mean": (a + b) / 2.0, "max": np.maximum(a, b), "min": np.minimum(a, b)}[op]
    else:
        raise ValueError("Неизвестная операция: " + op)
    return _to_uint8(r)


# линейное контрастирование
def linear_contrast(img, mode="minmax", p_low=1.0, p_high=99.0, lo=0, hi=255):
    h = np.bincount(img.ravel(), minlength=256)
    if mode == "minmax":
        nz = np.flatnonzero(h)
        lo, hi = int(nz[0]), int(nz[-1])
    elif mode == "percentile":
        cdf = np.cumsum(h) / h.sum() * 100.0
        lo = int(np.searchsorted(cdf, p_low))
        hi = int(np.searchsorted(cdf, p_high))
    lo, hi = int(lo), int(hi)
    if hi <= lo:
        return img.copy(), lo, hi
    lut = _to_uint8((np.arange(256) - lo) * 255.0 / (hi - lo))
    return lut[img], lo, hi


# глобальные пороги
def otsu_threshold(hist):
    p = hist / hist.sum()
    w0 = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    mu_t = mu[-1]
    denom = w0 * (1.0 - w0)
    sigma_b = np.zeros(256)
    ok = denom > 1e-12
    sigma_b[ok] = (mu_t * w0[ok] - mu[ok]) ** 2 / denom[ok]
    return int(np.argmax(sigma_b))


def triangle_threshold(hist):
    h = hist.astype(np.float64)
    n = len(h)
    nz = np.flatnonzero(h)
    lo, hi = int(nz[0]), int(nz[-1])
    peak = int(np.argmax(h))
    flip = (peak - lo) < (hi - peak)
    if flip:
        h = h[::-1]
        lo, hi, peak = n - 1 - hi, n - 1 - lo, n - 1 - peak
    if peak == lo:
        return peak
    x = np.arange(lo, peak + 1)
    dx, dy = peak - lo, h[peak] - h[lo]
    dist = np.abs(dy * (x - lo) - dx * (h[x] - h[lo]))
    t = int(x[np.argmax(dist)])
    return n - 1 - t if flip else t


def binarize(gray, t, light_object=True):
    mask = gray > t if light_object else gray <= t
    return mask.astype(np.uint8) * 255


def iou_f1(pred, truth):
    p, g = pred > 0, truth > 0
    tp = np.count_nonzero(p & g)
    fp = np.count_nonzero(p & ~g)
    fn = np.count_nonzero(~p & g)
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else 1.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 1.0
    return iou, f1
