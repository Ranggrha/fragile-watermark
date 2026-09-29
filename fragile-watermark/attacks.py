import io
import numpy as np
from PIL import Image


def _arr(img):
    return np.array(img.convert("RGB"))


def jpeg(q):
    def f(img):
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=q)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    return f


def crop_right(img, frac=0.25):
    a = _arr(img)
    a[:, int(a.shape[1] * (1 - frac)):] = 0
    return Image.fromarray(a)


def resize(img):
    w, h = img.size
    return img.resize((w // 2, h // 2), Image.BILINEAR).resize((w, h), Image.BILINEAR)


def noise(img, sigma=5):
    a = _arr(img).astype(float) + np.random.default_rng(0).normal(0, sigma, (img.size[1], img.size[0], 3))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def brightness(img, d=30):
    return Image.fromarray(np.clip(_arr(img).astype(int) + d, 0, 255).astype(np.uint8))


def contrast(img, k=1.3):
    return Image.fromarray(np.clip((_arr(img).astype(float) - 128) * k + 128, 0, 255).astype(np.uint8))


def copy_move(img):
    """Simulasi penyuntingan lokal: menempel area lain ke tengah citra."""
    a = _arr(img)
    h, w = a.shape[:2]
    s = h // 5
    y, x = (h - s) // 2, (w - s) // 2
    a[y:y + s, x:x + s] = a[10:10 + s, 10:10 + s].copy()
    return Image.fromarray(a)


ATTACKS = {
    "Edit lokal (copy-move)": copy_move,
    "JPEG Q90": jpeg(90), "JPEG Q70": jpeg(70), "JPEG Q50": jpeg(50),
    "Cropping (25% kanan dihitamkan)": crop_right,
    "Resize 50% lalu kembali": resize,
    "Gaussian noise (sigma 5)": noise,
    "Kecerahan +30": brightness,
    "Kontras x1.3": contrast,
}
