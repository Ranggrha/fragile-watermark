import io
import numpy as np
import streamlit as st
from PIL import Image
from attacks import ATTACKS
from experiments import run, to_xlsx
from metrics import ber, nc, psnr
from watermark import embed, logo_to_wm, tamper_overlay, text_to_wm, verify

st.set_page_config("Fragile Watermarking", layout="wide")

st.markdown("""
<style>
:root {
    color-scheme: dark;
    --ink: #edf5f4;
    --muted: #afc3c4;
    --line: rgba(223, 245, 244, 0.14);
    --glass: rgba(15, 36, 48, 0.62);
    --glass-strong: rgba(13, 31, 43, 0.82);
    --mint: #9ce4d1;
    --coral: #ffad87;
}

.stApp {
    color: var(--ink);
    background:
        radial-gradient(ellipse at 12% 0%, rgba(45, 125, 126, 0.24), transparent 36rem),
        radial-gradient(ellipse at 92% 18%, rgba(183, 94, 65, 0.19), transparent 32rem),
        linear-gradient(145deg, #08141d 0%, #102631 52%, #111c28 100%);
}
.stApp > header {
    background: transparent;
}
[data-testid="stAppViewContainer"] {
    background: transparent;
}
[data-testid="stMain"] > div {
    padding-top: clamp(1.4rem, 4vw, 3rem);
    padding-bottom: 3rem;
}
[data-testid="stMainBlockContainer"] {
    max-width: 1280px;
    padding-left: clamp(1rem, 4vw, 3rem);
    padding-right: clamp(1rem, 4vw, 3rem);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(19, 43, 54, 0.94), rgba(9, 25, 36, 0.96));
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.2rem 1rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] p {
    color: var(--muted);
    line-height: 1.65;
}
[data-testid="stFileUploader"],
[data-testid="stAlert"],
[data-testid="stDataFrame"],
[data-testid="stMetric"],
[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: var(--glass);
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.16);
}
[data-testid="stMetric"] {
    padding: 1rem 1.1rem;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}
[data-testid="stMetricLabel"] {
    color: var(--muted);
}
[data-testid="stMetricValue"] {
    color: var(--ink);
}
[data-testid="stTabs"] [role="tablist"] {
    gap: 0.45rem;
    padding: 0.35rem;
    border: 1px solid var(--line);
    border-radius: 16px;
    background: rgba(8, 23, 32, 0.55);
}
[data-testid="stTabs"] button[role="tab"] {
    min-height: 2.8rem;
    border-radius: 12px;
    color: var(--muted);
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--ink);
    background: rgba(156, 228, 209, 0.13);
}
[data-testid="stTabs"] [data-testid="stTabContent"] {
    padding-top: 1.5rem;
}
.stButton > button,
.stDownloadButton > button {
    min-height: 2.85rem;
    border: 1px solid rgba(175, 231, 215, 0.28);
    border-radius: 13px;
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.stButton > button[kind="primary"] {
    color: #10252a;
    background: linear-gradient(120deg, #a8ead2, #f0c09c);
    border: 0;
    font-weight: 700;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(175, 231, 215, 0.65);
}
[data-testid="stImage"] img {
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
}
input, textarea, [data-baseweb="select"] > div {
    border-radius: 12px !important;
}

@media (max-width: 760px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stTabs"] [role="tablist"] {
        overflow-x: auto;
        flex-wrap: nowrap;
    }
    [data-testid="stTabs"] button[role="tab"] {
        flex: 0 0 auto;
        font-size: 0.84rem;
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        gap: 0.8rem;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: min(100%, 280px);
        flex: 1 1 100%;
    }
    [data-testid="stMetric"] {
        padding: 0.8rem;
    }
    [data-testid="stMain"] > div {
        padding-top: 1.25rem;
    }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("show_app", False):
    st.markdown("""
    <style>
    .stApp {
        background: #07131f;
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
        min-height: min(68vh, 46rem);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 1rem 1.5rem;
    }
    .landing-kicker {
        margin-bottom: 1.2rem;
        padding: 0.55rem 0.9rem;
        border: 1px solid rgba(220, 245, 240, 0.2);
        border-radius: 999px;
        background: rgba(214, 245, 238, 0.08);
        color: #c4e9df;
        font-size: 0.82rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
    }
    .landing-title {
        margin: 0;
        color: #f4f0e8;
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.65rem, 8vw, 6.5rem);
        font-weight: 400;
        line-height: 1.02;
        letter-spacing: -0.035em;
    }
    .landing-subtitle {
        max-width: 36rem;
        margin: 1.4rem auto 2rem;
        color: #d1dfdc;
        font-size: clamp(0.95rem, 2.3vw, 1.1rem);
    }
    .landing-points {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.65rem;
        color: #d3e7e2;
        font-size: 0.82rem;
    }
    .landing-points span {
        padding: 0.55rem 0.8rem;
        border: 1px solid rgba(220, 245, 240, 0.16);
        border-radius: 999px;
        background: rgba(220, 245, 240, 0.07);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    @media (max-width: 600px) {
        .landing-content {
            min-height: 58vh;
            padding: 2rem 0.5rem 1rem;
        }
        .landing-title br {
            display: none;
        }
        .landing-points {
            gap: 0.45rem;
        }
        .landing-points span {
            font-size: 0.75rem;
        }
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
        <div class="landing-points">
            <span>Proteksi berbasis HMAC</span>
            <span>Peta area manipulasi</span>
            <span>Pengujian batch</span>
        </div>
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
