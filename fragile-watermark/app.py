import io
import numpy as np
import streamlit as st
from PIL import Image
from attacks import ATTACKS
from experiments import run, to_xlsx
from metrics import ber, nc, psnr
from watermark import embed, logo_to_wm, tamper_overlay, text_to_wm, verify

st.set_page_config("Fragile Watermarking", layout="wide")

if not st.session_state.get("show_app", False):
    st.markdown("""
    <style>
    .stApp {
        background: #07131f;
        overflow: hidden;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: -20%;
        z-index: 0;
        opacity: 0.6;
        background:
            linear-gradient(125deg, rgba(23, 111, 125, 0.9), transparent 45%),
            linear-gradient(235deg, rgba(219, 104, 55, 0.8), transparent 42%),
            linear-gradient(45deg, #07131f 20%, #164254 55%, #7c3f31 100%);
        background-size: 180% 180%;
        animation: watermark-drift 14s ease-in-out infinite alternate;
    }
    .stApp > header {
        background: transparent;
    }
    .landing-content {
        position: relative;
        z-index: 1;
        min-height: 68vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .landing-kicker {
        margin-bottom: 1rem;
        color: #b7d8d6;
        font-size: 0.82rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }
    .landing-title {
        margin: 0;
        color: #f4f0e8;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.8rem, 7vw, 6.5rem);
        font-weight: 400;
        line-height: 0.98;
    }
    .landing-subtitle {
        max-width: 38rem;
        margin: 1.4rem auto 2.2rem;
        color: #d1dfdc;
        font-size: 1rem;
    }
    @keyframes watermark-drift {
        0% { transform: translate3d(-3%, -2%, 0) scale(1); background-position: 0% 50%; }
        100% { transform: translate3d(3%, 2%, 0) scale(1.08); background-position: 100% 50%; }
    }
    </style>
    <main class="landing-content">
        <div class="landing-kicker">Fragile watermarking</div>
        <h1 class="landing-title">Manipulasi Citra<br>LSB + HMAC</h1>
        <p class="landing-subtitle">Sisipkan watermark kepemilikan dan deteksi manipulasi citra secara presisi.</p>
    </main>
    """, unsafe_allow_html=True)
    _, enter_col, _ = st.columns([1, 1.2, 1])
    with enter_col:
        if st.button("Masuk ke Aplikasi", type="primary", use_container_width=True, key="open_app"):
            st.session_state.show_app = True
            st.rerun()
    st.stop()

st.title("Fragile Watermarking LSB + HMAC: Deteksi Manipulasi Citra")
load = lambda f: Image.open(f).convert("RGB")
TYPES = ["png", "bmp", "jpg", "jpeg"]

with st.sidebar:
    if st.button("Halaman Awal", key="home_button"):
        st.session_state.show_app = False
        st.rerun()
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
