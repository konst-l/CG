"""
Генерация базы тестовых изображений (с эталонными масками объектов).
Запуск:  python make_test_images.py        ->  папки test_images/ и test_images/masks/
Нужны numpy и Pillow.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 360


def object_mask(rng, coverage, rmin, rmax):
    """Случайные эллипсы, прямоугольники и толстые линии до заданной доли покрытия."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for _ in range(4000):
        if np.count_nonzero(np.asarray(m)) / (W * H) >= coverage:
            break
        cx, cy = rng.integers(0, W), rng.integers(0, H)
        rx, ry = rng.integers(rmin, rmax + 1, size=2)
        kind = rng.integers(0, 3)
        if kind == 0:
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        elif kind == 1:
            d.rectangle([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        else:
            x2, y2 = cx + rng.integers(-3 * rmax, 3 * rmax), cy + rng.integers(-3 * rmax, 3 * rmax)
            d.line([cx, cy, x2, y2], fill=255, width=max(3, rmin))
    return m


def compose(mask, bg, fg, sigma=0.0, blur=0.0, ramp=None, seed=0):
    """Яркость фона bg, объектов fg, затем размытие, неравномерное освещение, шум."""
    rng = np.random.default_rng(seed)
    soft = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64) / 255.0
    img = bg * (1 - soft) + fg * soft
    if blur > 0:
        img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
                         .filter(ImageFilter.GaussianBlur(blur)), dtype=np.float64)
    if ramp is not None:                         # множитель освещённости слева направо
        img = img * np.linspace(ramp[0], ramp[1], W)[None, :]
    img = img + rng.normal(0, sigma, img.shape)
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def save(arr, name, mask=None):
    os.makedirs("test_images/masks", exist_ok=True)
    Image.fromarray(arr).save(f"test_images/{name}.png")
    if mask is not None:
        mask.save(f"test_images/masks/{name}_mask.png")


def main():
    big = lambda s: object_mask(np.random.default_rng(s), 0.35, 25, 55)       # крупные объекты, ~35 %
    small = lambda s: object_mask(np.random.default_rng(s), 0.015, 5, 9)      # мелкие объекты, ~1.5 %

    m = big(1)
    # Тёмные объекты на светлом фоне
    save(compose(m, 200, 60, sigma=10, seed=1), "01_bimodal_dark_objects", m)
    save(compose(m, 170, 90, sigma=35, seed=2), "03_noisy", m)
    save(compose(m, 200, 60, sigma=6, blur=4, seed=3), "04_blurred", m)
    save(compose(m, 125, 105, sigma=2.5, seed=4), "05_low_contrast", m)
    save(compose(m, 190, 90, sigma=8, ramp=(0.45, 1.0), seed=5), "06_uneven_illumination", m)
    save(compose(m, 245, 190, sigma=5, seed=9), "08_overexposed", m)

    # Светлые мелкие объекты на тёмном фоне: гистограмма с одним пиком и хвостом
    s = small(7)
    # (фон неравномерно освещён, поэтому его гистограмма широкая, а объектов мало)
    save(compose(s, 80, 200, sigma=8, ramp=(0.5, 1.0), seed=6), "02_small_light_objects", s)
    save(compose(s, 80, 190, sigma=6, blur=1.2, ramp=(0.6, 1.0), seed=11), "09_small_light_blurred", s)

    # Недосвеченный снимок (светлые объекты на тёмном фоне)
    m2 = big(8)
    save(compose(m2, 12, 52, sigma=3, seed=10), "07_underexposed", m2)

    # Цветное малоконтрастное
    m3 = big(12)
    soft = np.asarray(m3.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64)[..., None] / 255.0
    bg, fg = np.array([150, 140, 125.0]), np.array([125, 128, 133.0])
    rng = np.random.default_rng(13)
    col = bg * (1 - soft) + fg * soft + rng.normal(0, 3, (H, W, 3))
    save(np.clip(np.rint(col), 0, 255).astype(np.uint8), "10_color_low_contrast")

    # Градиент (для проверки операций над двумя изображениями)
    g = np.tile(np.linspace(0, 255, W).astype(np.uint8), (H, 1))
    save(g, "11_gradient_for_binary_ops")
    print("Готово: папка test_images/")


if __name__ == "__main__":
    main()
