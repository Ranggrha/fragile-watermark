import numpy as np
import pandas as pd
from attacks import ATTACKS
from metrics import psnr, nc, ber
from watermark import embed, verify


def run(images: dict, password: str, wm: np.ndarray) -> pd.DataFrame:
    rows = []
    for name, img in images.items():
        st = embed(img, password, wm)
        p = psnr(np.array(img.convert("RGB")), np.array(st))
        for an, fn in [("Tanpa serangan", lambda x: x)] + list(ATTACKS.items()):
            r = verify(fn(st), password)
            rows.append({"Citra": name, "Serangan": an, "PSNR_dB": round(p, 2),
                         "Blok_asli_%": round(100 * r["authentic"], 2),
                         "NC": round(nc(wm, r["wm"]), 4), "BER": round(ber(wm, r["wm"]), 4)})
    return pd.DataFrame(rows)


def to_xlsx(df: pd.DataFrame, target):
    with pd.ExcelWriter(target, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Hasil", index=False)
        df.pivot_table(index="Serangan", values=["Blok_asli_%", "NC", "BER"], aggfunc="mean").round(4) \
          .to_excel(w, sheet_name="Rata-rata")
