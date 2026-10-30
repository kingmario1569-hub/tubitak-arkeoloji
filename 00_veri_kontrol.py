"""ADIM 0: Yerleşim veri setini denetler ve başla/durdur kararını verir.

Girdi : veri/yerlesimler_temiz.csv  (öğrencinin kaynaklardan derlediği tablo)
Çıktı : sonuclar/veri_kontrol.json  ve ekrana rapor

Bu betik hiçbir veriyi DEĞİŞTİRMEZ; sadece sorunları listeler.
Sorunları kaynağa bakarak elle düzeltin ve veri/TEMIZLEME_GUNLUGU.md'ye yazın.

Çalıştırma:  python 00_veri_kontrol.py
"""
import json
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
import ortak as o

ZORUNLU = ["site_id", "ad", "lat", "lon", "koord_kesinlik", "donemler",
           "ilk_donem", "tek_donemli", "kaynak", "kaynak_kayit"]


def main():
    o.klasorleri_hazirla()
    df = pd.read_csv(o.YERLESIM_CSV)
    hatalar, uyarilar = [], []

    eksik = [s for s in ZORUNLU if s not in df.columns]
    if eksik:
        raise SystemExit(f"Eksik sütun(lar): {eksik}. Veri sözlüğüne bakın (Protokol §4.1).")

    # 1) Boş hücreler
    for s in ZORUNLU:
        n = df[s].isna().sum()
        if n:
            hatalar.append(f"'{s}' sütununda {n} boş hücre var.")

    # 2) Kimlik tekrarları
    tekrar = df[df["site_id"].duplicated(keep=False)]
    if len(tekrar):
        hatalar.append(f"Tekrarlanan site_id: {sorted(tekrar['site_id'].unique())[:10]}")

    # 3) Değer aralıkları
    if not df["lat"].between(35, 43).all() or not df["lon"].between(25, 45).all():
        kotu = df[~(df["lat"].between(35, 43) & df["lon"].between(25, 45))]
        hatalar.append(f"Türkiye sınırları dışında {len(kotu)} koordinat (enlem/boylam ters yazılmış olabilir): "
                       f"{kotu['site_id'].tolist()[:10]}")
    if not df["ilk_donem"].isin(o.DONEMLER).all():
        hatalar.append(f"ilk_donem yalnızca {o.DONEMLER} olabilir. Bulunan: {sorted(df['ilk_donem'].unique())}")
    if not df["koord_kesinlik"].isin([1, 2, 3]).all():
        hatalar.append("koord_kesinlik yalnızca 1, 2 veya 3 olabilir.")
    if not df["tek_donemli"].isin(["evet", "hayir", "hayır"]).all():
        hatalar.append("tek_donemli yalnızca 'evet' veya 'hayir' olabilir.")

    # 4) Birbirine 1 km'den yakın kayıtlar (aynı yerleşim iki kez girilmiş olabilir)
    koord = np.radians(df[["lat", "lon"]].to_numpy())
    agac = BallTree(koord, metric="haversine")
    komsular = agac.query_radius(koord, r=1.0 / 6371.0)
    yakin = sorted({tuple(sorted((df.site_id[i], df.site_id[j])))
                    for i, ks in enumerate(komsular) for j in ks if i != j})
    if yakin:
        uyarilar.append(f"Birbirine 1 km'den yakın {len(yakin)} çift var (aynı yerleşim mi? kontrol edin): {yakin[:10]}")

    # 5) Başla / durdur sayımı (kesinliği 3 olanlar analizde kullanılmayacağı için sayılmaz)
    kullanilacak = df[df["koord_kesinlik"] != 3]
    sayim = kullanilacak["ilk_donem"].value_counts().reindex(o.DONEMLER, fill_value=0)
    en_az, en_cok = int(sayim.min()), int(sayim.max())
    oran = en_cok / en_az if en_az else float("inf")
    if en_az >= 80 and oran <= o.EN_FAZLA_DENGESIZLIK:
        karar = "BAŞLA: Tam tasarım (Analiz A + B)."
    elif en_az >= o.EN_AZ_YERLESIM:
        karar = "BAŞLA (sınırlı): Analiz A + istatistik. Dengesizlik fazlaysa kalabalık dönemden mekânsal alt örnek alın." \
            if oran > o.EN_FAZLA_DENGESIZLIK else "BAŞLA (sınırlı): Analiz A + istatistik."
    else:
        karar = f"DURDUR: En az bir dönemde {o.EN_AZ_YERLESIM}'den az yerleşim var. Bölgeyi genişletin."

    rapor = {
        "toplam_kayit": int(len(df)),
        "analize_girecek": int(len(kullanilacak)),
        "donem_sayilari": {k: int(v) for k, v in sayim.items()},
        "dengesizlik_orani": round(oran, 2),
        "kaynak_sayilari": kullanilacak["kaynak"].value_counts().to_dict(),
        "kesinlik_sayilari": df["koord_kesinlik"].value_counts().sort_index().astype(int).to_dict(),
        "tek_donemli_sayisi": int(kullanilacak["tek_donemli"].eq("evet").sum()),
        "hatalar": hatalar,
        "uyarilar": uyarilar,
        "karar": karar,
    }
    (o.SONUC / "veri_kontrol.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== VERİ KONTROL RAPORU ===")
    for k, v in rapor.items():
        if k not in ("hatalar", "uyarilar"):
            print(f"{k}: {v}")
    print("\nHATALAR (düzeltilmeden devam etmeyin):" if hatalar else "\nHata yok.")
    for h in hatalar:
        print("  ✗", h)
    for u in uyarilar:
        print("  ⚠", u)
    if hatalar:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
