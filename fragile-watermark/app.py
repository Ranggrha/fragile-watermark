import io
import numpy as np
import streamlit as st
from PIL import Image
from attacks import ATTACKS
from experiments import run, to_xlsx
from metrics import ber, nc, psnr
from watermark import embed, logo_to_wm, tamper_overlay, text_to_wm, verify

st.set_page_config("Fragile Watermarking", layout="wide")
st.title("Fragile Watermarking LSB + HMAC: Deteksi Manipulasi Citra")
load = lambda f: Image.open(f).convert("RGB")
TYPES = ["png", "bmp", "jpg", "jpeg"]

with st.sidebar:
    key = st.text_input("Kunci rahasia", type="password")
    mode = st.radio("Watermark", ["Teks / NPM", "Logo biner"])
    if mode.startswith("Teks"):
        wm = text_to_wm(st.text_input("Teks identitas (maks 40 karakter)", "NPM 1234567890"))
    else:
        lf = st.file_uploader("Logo", type=["png", "jpg", "jpeg"])
        wm = logo_to_wm(Image.open(lf)) if lf else None
    if wm is not None:
        st.image(wm * 255, caption="Watermark 64x64", width=128, clamp=True)

t1, t2, t3 = st.tabs(["1. Sisipkan", "2. Serang & Verifikasi", "3. Pengujian batch"])

with t1:
    f = st.file_uploader("Citra asli (min 256x256)", type=TYPES, key="orig_upload")
    if f and st.button("Sisipkan watermark"):
        if not key or wm is None:
            st.error("Isi kunci dan watermark di sidebar.")
        else:
            try:
                o = load(f)
                st.session_state.update(orig=o, stego=embed(o, key, wm))
            except ValueError as e:
                st.error(str(e))
    if "stego" in st.session_state:
        o, s = st.session_state["orig"], st.session_state["stego"]
        c1, c2 = st.columns(2)
        c1.image(o, "Citra asli")
        c2.image(s, "Citra ber-watermark")
        st.metric("PSNR", f"{psnr(np.array(o), np.array(s)):.2f} dB")
        buf = io.BytesIO()
        s.save(buf, "PNG")
        st.download_button("Unduh PNG (jangan simpan sebagai JPEG)", buf.getvalue(), "stego.png", "image/png")

with t2:
    up = st.file_uploader("Citra yang diverifikasi (kosongkan untuk memakai hasil tab 1)", type=TYPES, key="ver")
    src = load(up) if up else st.session_state.get("stego")
    an = st.selectbox("Serangan", ["Tanpa serangan"] + list(ATTACKS))
    if src is not None and st.button("Verifikasi"):
        if not key:
            st.error("Isi kunci rahasia di sidebar.")
        else:
            try:
                img = src if an == "Tanpa serangan" else ATTACKS[an](src)
                r = verify(img, key)
                a, b, c = st.columns(3)
                a.image(img, "Citra yang diuji")
                b.image(tamper_overlay(img, r["valid_map"]), "Peta manipulasi (merah = diubah)")
                c.image(r["wm"] * 255, "Watermark hasil ekstraksi", clamp=True)
                m1, m2, m3 = st.columns(3)
                m1.metric("Blok asli", f"{100 * r['authentic']:.2f}%")
                if wm is not None:
                    m2.metric("NC", f"{nc(wm, r['wm']):.4f}")
                    m3.metric("BER", f"{ber(wm, r['wm']):.4f}")
                if r["authentic"] > 0.9999:
                    st.success("Citra ASLI: seluruh blok terverifikasi.")
                elif r["authentic"] == 0:
                    st.error("Semua blok gagal: citra dimanipulasi berat, atau kunci salah.")
                else:
                    st.warning("Citra DIMANIPULASI pada area berwarna merah.")
            except ValueError as e:
                st.error(str(e))

with t3:
    files = st.file_uploader("Citra uji (minimal 5)", type=TYPES, accept_multiple_files=True, key="batch")
    if files and st.button("Jalankan semua serangan"):
        if not key or wm is None:
            st.error("Isi kunci dan watermark di sidebar.")
        else:
            with st.spinner("Memproses..."):
                df = run({f.name: load(f) for f in files}, key, wm)
            st.dataframe(df, use_container_width=True)
            buf = io.BytesIO()
            to_xlsx(df, buf)
            st.download_button("Unduh hasil (XLSX)", buf.getvalue(), "hasil_pengujian.xlsx")
