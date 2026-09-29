# Fragile Watermarking LSB + HMAC-SHA256

Aplikasi web (Streamlit) untuk menyisipkan watermark kepemilikan dan mendeteksi manipulasi citra beserta peta area yang diubah.

**Anggota:** Nama - NPM (isi sendiri)

## Instalasi
```
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
## Menjalankan
```
streamlit run app.py
pytest -q
```
## Cara pakai
1. Sidebar: isi kunci rahasia dan watermark (teks/NPM atau logo).
2. Tab 1: unggah citra (PNG/BMP, min 256x256), sisipkan, unduh hasil PNG.
3. Tab 2: pilih serangan lalu verifikasi. Merah = blok diubah. Tampil NC dan BER.
4. Tab 3: unggah >=5 citra untuk tabel pengujian otomatis, unduh XLSX.

## Cara kerja singkat
Citra dibagi blok 8x8 RGB (192 LSB per blok): 64 bit tag `HMAC-SHA256(kunci, 7 bit atas blok + indeks blok + ukuran citra + payload)` dan 128 bit potongan watermark (64x64 bit, diacak PRNG dari kunci, diulang di seluruh citra). Verifikasi menghitung ulang tag; watermark diekstrak dengan majority voting hanya dari blok yang lolos.

Kunci diturunkan dengan PBKDF2-HMAC-SHA256 (100.000 iterasi). Kunci tidak disimpan di kode.
