"""Fragile watermarking LSB berbasis HMAC-SHA256 (logika ditulis sendiri).

Tiap blok 8x8 piksel RGB punya 192 slot LSB:
  64 bit  -> tag HMAC-SHA256 (dipotong) dari isi blok
  128 bit -> potongan watermark 64x64 (4096 bit) yang diacak dengan kunci
Blok yang diubah -> tag tidak cocok -> ditandai pada peta manipulasi.
"""
import hashlib, hmac, struct
from functools import lru_cache
import cv2
import numpy as np
from PIL import Image

B = 8
WM_SHAPE = (64, 64)
WM_BITS = WM_SHAPE[0] * WM_SHAPE[1]
TAG_BITS, PAY_BITS = 64, 128
MIN_SIDE = 256


@lru_cache(maxsize=8)
def derive_key(password: str) -> bytes:
    if not password:
        raise ValueError("Kunci rahasia tidak boleh kosong.")
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"fragile-wm-v1", 100_000, 32)


def text_to_wm(text: str) -> np.ndarray:
    text = (text.strip() or "WM")[:40]
    canvas = np.zeros(WM_SHAPE, np.uint8)
    for n, i in enumerate(range(0, len(text), 8)):
        cv2.putText(canvas, text[i:i + 8], (2, 12 + 12 * n), cv2.FONT_HERSHEY_SIMPLEX, 0.35, 255, 1, cv2.LINE_AA)
    return (canvas > 100).astype(np.uint8)


def logo_to_wm(img: Image.Image) -> np.ndarray:
    g = cv2.resize(np.array(img.convert("L")), WM_SHAPE[::-1], interpolation=cv2.INTER_AREA)
    _, b = cv2.threshold(g, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return b.astype(np.uint8)


def _prep(img):
    a = np.array(img.convert("RGB"), dtype=np.uint8)
    H, W = a.shape[:2]
    if min(H, W) < MIN_SIDE:
        raise ValueError(f"Citra terlalu kecil (minimal {MIN_SIDE}x{MIN_SIDE} piksel).")
    return a, H, W


def _blocks(a):
    H8, W8 = a.shape[0] // B, a.shape[1] // B
    c = a[:H8 * B, :W8 * B]
    return c.reshape(H8, B, W8, B, 3).transpose(0, 2, 1, 3, 4).reshape(H8 * W8, -1), H8, W8


def _unblocks(bl, a, H8, W8):
    out = a.copy()
    out[:H8 * B, :W8 * B] = bl.reshape(H8, W8, B, B, 3).transpose(0, 2, 1, 3, 4).reshape(H8 * B, W8 * B, 3)
    return out


def _perm(key):
    return np.random.default_rng(int.from_bytes(key[:8], "big")).permutation(WM_BITS)


def _idx(nb):
    return (np.arange(nb)[:, None] * PAY_BITS + np.arange(PAY_BITS)[None, :]) % WM_BITS


def _tags(upper, pay, key, H, W):
    head = struct.pack(">II", H, W)
    packed = np.packbits(pay, axis=1)
    out = np.empty((len(upper), TAG_BITS), np.uint8)
    for i in range(len(upper)):
        msg = head + struct.pack(">I", i) + upper[i].tobytes() + packed[i].tobytes()
        out[i] = np.unpackbits(np.frombuffer(hmac.digest(key, msg, "sha256")[:TAG_BITS // 8], np.uint8))
    return out


def embed(img: Image.Image, password: str, wm: np.ndarray) -> Image.Image:
    key = derive_key(password)
    a, H, W = _prep(img)
    bl, H8, W8 = _blocks(a)
    upper = bl & 0xFE
    pay = wm.reshape(-1)[_perm(key)][_idx(len(bl))].astype(np.uint8)
    lsb = np.concatenate([_tags(upper, pay, key, H, W), pay], axis=1)
    return Image.fromarray(_unblocks(upper | lsb, a, H8, W8))


def verify(img: Image.Image, password: str) -> dict:
    key = derive_key(password)
    a, H, W = _prep(img)
    bl, H8, W8 = _blocks(a)
    upper, lsb = bl & 0xFE, bl & 1
    tag, pay = lsb[:, :TAG_BITS], lsb[:, TAG_BITS:]
    ok = (_tags(upper, pay, key, H, W) == tag).all(axis=1)
    v = _idx(len(bl))[ok].ravel()
    ones = np.bincount(v, weights=pay[ok].ravel(), minlength=WM_BITS)
    tot = np.bincount(v, minlength=WM_BITS)
    wm = np.zeros(WM_BITS, np.uint8)
    wm[_perm(key)] = (ones * 2 > tot).astype(np.uint8)  # majority voting dari blok asli saja
    return {"valid_map": ok.reshape(H8, W8), "authentic": float(ok.mean()), "wm": wm.reshape(WM_SHAPE)}


def tamper_overlay(img: Image.Image, valid_map: np.ndarray) -> Image.Image:
    a = np.array(img.convert("RGB"))
    h, w = valid_map.shape[0] * B, valid_map.shape[1] * B
    m = np.kron(~valid_map, np.ones((B, B), bool))
    reg = a[:h, :w]
    reg[m] = (0.4 * reg[m] + 0.6 * np.array([255, 0, 0])).astype(np.uint8)
    return Image.fromarray(a)
