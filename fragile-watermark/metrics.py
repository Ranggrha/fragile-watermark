import numpy as np


def mse(a, b):
    return float(np.mean((np.asarray(a, float) - np.asarray(b, float)) ** 2))


def psnr(a, b):
    m = mse(a, b)
    return float("inf") if m == 0 else float(10 * np.log10(255.0 ** 2 / m))


def nc(w1, w2):
    w1, w2 = w1.astype(float), w2.astype(float)
    d = np.sqrt((w1 ** 2).sum() * (w2 ** 2).sum())
    return float((w1 * w2).sum() / d) if d else 0.0


def ber(w1, w2):
    return float(np.mean(w1 != w2))
