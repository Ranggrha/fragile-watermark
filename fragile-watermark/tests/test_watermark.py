import os, sys
import numpy as np
import pytest
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from attacks import copy_move, crop_right, jpeg
from metrics import ber, nc, psnr
from watermark import embed, text_to_wm, verify

KEY = "kunci-uji"


@pytest.fixture(scope="module")
def img():
    y, x = np.mgrid[:288, :320]
    a = np.stack([x * 255 // 320, y * 255 // 288, (x + y) % 256], -1).astype(np.uint8)
    return Image.fromarray(a)


@pytest.fixture(scope="module")
def wm():
    return text_to_wm("NPM 123")


@pytest.fixture(scope="module")
def stego(img, wm):
    return embed(img, KEY, wm)


def test_roundtrip_utuh(stego, wm):
    r = verify(stego, KEY)
    assert r["authentic"] == 1.0 and ber(wm, r["wm"]) == 0 and nc(wm, r["wm"]) == 1.0


def test_psnr_tinggi(img, stego):
    assert psnr(np.array(img), np.array(stego)) > 48


def test_kunci_salah(stego):
    assert verify(stego, "salah")["authentic"] == 0


def test_edit_lokal_terdeteksi_dan_watermark_selamat(stego, wm):
    r = verify(copy_move(stego), KEY)
    assert 0.9 < r["authentic"] < 1.0 and ber(wm, r["wm"]) == 0


def test_jpeg_merusak_semua(stego):
    assert verify(jpeg(90)(stego), KEY)["authentic"] < 0.05


def test_crop_sebagian(stego):
    assert 0.7 < verify(crop_right(stego), KEY)["authentic"] < 0.8


def test_citra_terlalu_kecil(wm):
    with pytest.raises(ValueError):
        embed(Image.new("RGB", (100, 100)), KEY, wm)


def test_metrik():
    w = np.array([[1, 0], [0, 1]], np.uint8)
    assert psnr(w, w) == float("inf") and nc(w, w) == 1.0 and ber(w, 1 - w) == 1.0
