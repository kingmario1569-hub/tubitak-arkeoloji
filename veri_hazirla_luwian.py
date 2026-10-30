"""ADIM 0a: LuwianSiteAtlas dosyalarını proje tablosu biçimine dönüştürür.

Kaynak: LuwianSiteAtlas (Zenodo, DOI 10.5281/zenodo.17128262, CC BY 4.0)
Girdi : veri/kaynak/luwian/sites.csv, site_period.csv, ore_deposits_WA.csv
Çıktı :
  veri/yerlesimler_temiz.csv          Proje tablosu (00_veri_kontrol.py'nin beklediği biçim)
  veri/madenler.csv                   Maden yatakları (Drive'daki tubitak-veri klasörüne kopyalanır)
  veri/luwian_donusum_raporu.md       Hangi kayıt neden çıkarıldı, dönem eşleştirme tablosu

Bu betik hiçbir değer UYDURMAZ: Koordinatlar ve dönemler kaynaktan olduğu gibi alınır.
Kurallar aşağıda açıkça yazılıdır; değiştirilirse ON_KAYIT.md'ye not edilmelidir.

Çalıştırma:  python veri_hazirla_luwian.py
"""
import re
import pandas as pd
import ortak as o

KAYNAK = o.VERI / "kaynak" / "luwian"

# --- Dönem eşleştirme tablosu (kaynaktaki kod -> projedeki ana dönem) ---
# Soru işaretli (belirsiz) kayıtlar ilk dönem hesabında KULLANILMAZ.
NEOLITIK = {"N", "LN", "N-ECh"}            # N-ECh: Neolitik–Erken Kalkolitik geçişi; en erken ucu alınır
KALKOLITIK = {"Ch", "ECh", "Ech", "MCh", "LCh"}
TUNC_DESEN = re.compile(r"^(EBA|MBA|LBA)")  # EBA, EBA 1, EBA 2-3, MBA, LBA, "EBA LBA" ...
SIRA = {"Neolitik": 0, "Kalkolitik": 1, "Tunc": 2}

# --- Analize alınmayacak yerleşim türleri (sites.csv, site_type_id) ---
# Kaynakta tür kodlarının adları verilmemiştir; aşağıdaki kararlar kayıt adlarına bakılarak verildi
# ve öğretmen/danışman tarafından gözden geçirilmelidir.
CIKARILAN_TURLER = {
    3: "Kaya anıtı / yazıt (yerleşim değil; ör. Karabel)",
    6: "Yazılı kaynaklardaki yer adı (konumu arkeolojik olarak belirlenmemiş; ör. Wilusa, Kuwaliya)",
    11: "Ege adası (Türkiye dışı; ör. Rodos)",
    15: "Ege adası (Türkiye dışı; ör. Midilli, Sakız)",
}


def ana_donem(kod):
    if not isinstance(kod, str):
        return None
    k = kod.strip().rstrip(".;")
    if "?" in k:
        return None
    if k in NEOLITIK:
        return "Neolitik"
    if k in KALKOLITIK:
        return "Kalkolitik"
    if TUNC_DESEN.match(k):
        return "Tunc"
    return None  # Paleolitik, Demir Çağı ve sonrası, tanımsız kodlar


def main():
    siteler = pd.read_csv(KAYNAK / "sites.csv")
    donem = pd.read_csv(KAYNAK / "site_period.csv")
    rapor, cikan = [], []

    donem["ana"] = donem["period_name"].map(ana_donem)
    eslesme = (donem.dropna(subset=["period_name"])
               .groupby("period_name")["ana"].first().fillna("— (kullanılmadı)").reset_index())

    ozet = (donem.dropna(subset=["ana"]).groupby("site_number")
            .agg(donemler=("ana", lambda s: ";".join(sorted(set(s), key=SIRA.get))),
                 ilk_donem=("ana", lambda s: min(s, key=SIRA.get)),
                 donem_sayisi=("ana", lambda s: len(set(s)))))
    ham_donemler = donem.dropna(subset=["period_name"]).groupby("site_number")["period_name"].apply(
        lambda s: ";".join(s.astype(str)))

    b, g, d, k = o.BOLGE_SINIRI
    tablo = []
    for _, s in siteler.iterrows():
        sebep = None
        tur = s["site_type_id"]
        if pd.notna(tur) and int(tur) in CIKARILAN_TURLER:
            sebep = CIKARILAN_TURLER[int(tur)]
        elif not (b <= s["longitude"] <= d and g <= s["latitude"] <= k):
            sebep = "Çalışma bölgesi dışında"
        elif s["id"] not in ozet.index:
            sebep = "Neolitik, Kalkolitik veya Tunç Çağı dönem kaydı yok"
        if sebep:
            cikan.append({"id": s["id"], "ad": str(s["name"]).strip(), "sebep": sebep})
            continue
        z = ozet.loc[s["id"]]
        tablo.append({
            "site_id": f"LSA_{int(s['id']):04d}",
            "ad": str(s["name"]).strip(),
            "lat": round(float(s["latitude"]), 6),
            "lon": round(float(s["longitude"]), 6),
            "koord_kesinlik": 1,   # Kaynakta kesinlik bilgisi yok; uydu kontrolüyle doğrulanacak (Protokol §5.2)
            "donemler": z["donemler"],
            "ilk_donem": z["ilk_donem"],
            "tek_donemli": "evet" if z["donem_sayisi"] == 1 else "hayir",
            "kaynak": "LuwianSiteAtlas",
            "kaynak_kayit": s["full_url"] if pd.notna(s["full_url"]) else f"sites.csv id={s['id']}",
            "kaynak_donem_kodlari": ham_donemler.get(s["id"], ""),
            "luwian_tur_kodu": "" if pd.isna(tur) else int(tur),
        })
    tablo = pd.DataFrame(tablo)
    tablo.to_csv(o.YERLESIM_CSV, index=False)

    # --- Maden yatakları ---
    m = pd.read_csv(KAYNAK / "ore_deposits_WA.csv")
    madenler = pd.DataFrame({"lat": m["Latitude"], "lon": m["Longitude"], "tur": m["Description"],
                             "ad": m["Ore"], "kaynak": "LuwianSiteAtlas ore_deposits_WA; " + m["Reference"]})
    madenler.to_csv(o.VERI / "madenler.csv", index=False)

    # --- Rapor ---
    cikan = pd.DataFrame(cikan)
    sayim = tablo["ilk_donem"].value_counts().reindex(o.DONEMLER, fill_value=0)
    with open(o.VERI / "luwian_donusum_raporu.md", "w", encoding="utf-8") as f:
        f.write("# LuwianSiteAtlas dönüşüm raporu\n\n")
        f.write(f"- Kaynaktaki yerleşim sayısı: {len(siteler)}\n")
        f.write(f"- Tabloya alınan: {len(tablo)}\n- Çıkarılan: {len(cikan)}\n\n")
        f.write("## İlk iskân dönemine göre sayılar\n\n| Dönem | Sayı |\n|---|---|\n")
        for dn, v in sayim.items():
            f.write(f"| {dn} | {v} |\n")
        f.write("\n## Çıkarma sebepleri\n\n| Sebep | Sayı |\n|---|---|\n")
        for sb, v in cikan["sebep"].value_counts().items():
            f.write(f"| {sb} | {v} |\n")
        f.write("\n## Dönem eşleştirme tablosu\n\n| Kaynaktaki kod | Projedeki dönem |\n|---|---|\n")
        for _, r in eslesme.iterrows():
            f.write(f"| `{r.period_name}` | {r.ana} |\n")
        f.write("\n## Çıkarılan kayıtların listesi\n\n| id | Ad | Sebep |\n|---|---|---|\n")
        for _, r in cikan.iterrows():
            f.write(f"| {r.id} | {r.ad} | {r.sebep} |\n")
        f.write(f"\n## Maden yatakları\n\n{len(madenler)} kayıt `veri/madenler.csv` dosyasına yazıldı.\n")

    print(f"Tabloya alınan: {len(tablo)} · Çıkarılan: {len(cikan)}")
    print("İlk iskân dönemine göre:", sayim.to_dict())
    print(f"Maden yatağı: {len(madenler)}")
    print("Ayrıntı: veri/luwian_donusum_raporu.md")


if __name__ == "__main__":
    main()
