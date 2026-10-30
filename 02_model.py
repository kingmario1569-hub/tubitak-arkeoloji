"""ADIM 2: İstatistik testleri, Random Forest modeli ve hipotezlerin değerlendirilmesi.

Girdi : sonuclar/degiskenler.csv   (01_degisken_hesapla.py'nin çıktısı)
Çıktı : sonuclar/ klasöründe
  istatistik.csv          Her değişken için Kruskal-Wallis, epsilon-kare, dönem ortancaları
  ikili_testler.csv       Dönem çiftleri için Mann-Whitney U (Bonferroni düzeltmeli)
  model_metrikleri.json   Mekânsal ve rastgele doğrulama, lojistik regresyon, etiket karıştırma testi
  karmasiklik.csv         Mekânsal doğrulamada karmaşıklık matrisi
  onem.csv                Permütasyon önemi (önyargı değişkenleri dahil / hariç)
  kayma.csv               İkili karşılaştırmalarda değişken önemi (Neolitik→Kalkolitik, Kalkolitik→Tunç)
  duyarlilik.csv          Duyarlılık analizleri
  hipotezler.csv          H1–H4 ve H0 için "destekleniyor / desteklenmiyor" kararı
  grafikler/*.png

ÖN-KAYIT KURALI: Bu betiği ilk kez çalıştırmadan ÖNCE ON_KAYIT.md commit'lenmiş olmalı.
Eşikler ve hipotezler ortak.py'de; sonuca bakıp değiştirmeyin.

Çalıştırma:  python 02_model.py
"""
import json
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, permutation_test_score
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.inspection import permutation_importance, PartialDependenceDisplay
import sklearn

import ortak as o

warnings.filterwarnings("ignore", category=UserWarning)
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "font.size": 9})
RENK = {"Neolitik": "#3a7d44", "Kalkolitik": "#c07a2c", "Tunc": "#6b4f9e"}


# ---------------------------------------------------------------------------
# VERİ
# ---------------------------------------------------------------------------
def veriyi_yukle():
    df = pd.read_csv(o.DEGISKEN_CSV)
    df = df[df["ilk_donem"].isin(o.DONEMLER)].copy()
    degiskenler = [d for d in o.TEMALAR if d in df.columns]
    once = len(df)
    df = df.dropna(subset=degiskenler).reset_index(drop=True)
    print(f"{once} yerleşimden {once - len(df)} tanesi eksik değer nedeniyle çıkarıldı. Kalan: {len(df)}")
    # Mekânsal bloklar: UTM koordinatlarını BLOK_BOYUTU_M'lik karelere böl
    g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    g = g.to_crs(o.utm_epsg(df.lon.mean()))
    df["x_m"], df["y_m"] = g.geometry.x.to_numpy(), g.geometry.y.to_numpy()
    df["blok"] = ((df.x_m // o.BLOK_BOYUTU_M).astype(int).astype(str) + "_" +
                  (df.y_m // o.BLOK_BOYUTU_M).astype(int).astype(str))
    return df, degiskenler


# ---------------------------------------------------------------------------
# 1) İSTATİSTİK (H1–H3)
# ---------------------------------------------------------------------------
def istatistik(df, degiskenler):
    satirlar, ikili = [], []
    k, n = len(o.DONEMLER), len(df)
    for d in degiskenler:
        gruplar = [df.loc[df.ilk_donem == p, d] for p in o.DONEMLER]
        H, p = stats.kruskal(*gruplar)
        eps2 = max(0.0, (H - k + 1) / (n - k))         # Kruskal-Wallis epsilon-kare
        satir = {"degisken": d, "tema": o.TEMALAR[d], "H": H, "p": p, "epsilon2": eps2}
        for donem, grup in zip(o.DONEMLER, gruplar):
            satir[f"ortanca_{donem}"] = grup.median()
        satirlar.append(satir)
        # İkili karşılaştırmalar (Dunn testi yerine Mann-Whitney U + Bonferroni)
        ciftler = [(a, b) for i, a in enumerate(o.DONEMLER) for b in o.DONEMLER[i + 1:]]
        for a, b in ciftler:
            U, pu = stats.mannwhitneyu(df.loc[df.ilk_donem == a, d], df.loc[df.ilk_donem == b, d])
            ikili.append({"degisken": d, "donem_1": a, "donem_2": b,
                          "ortanca_1": df.loc[df.ilk_donem == a, d].median(),
                          "ortanca_2": df.loc[df.ilk_donem == b, d].median(),
                          "U": U, "p_bonferroni": min(1.0, pu * len(ciftler))})
    ist, ik = pd.DataFrame(satirlar), pd.DataFrame(ikili)
    ist.to_csv(o.SONUC / "istatistik.csv", index=False)
    ik.to_csv(o.SONUC / "ikili_testler.csv", index=False)

    # Kutu grafikleri
    sutun = 3
    satir = int(np.ceil(len(degiskenler) / sutun))
    fig, eksenler = plt.subplots(satir, sutun, figsize=(4 * sutun, 3 * satir))
    for ax, d in zip(np.ravel(eksenler), degiskenler):
        veri = [df.loc[df.ilk_donem == p, d] for p in o.DONEMLER]
        kutu = ax.boxplot(veri, tick_labels=o.DONEMLER, patch_artist=True, showfliers=False)
        for parca, p in zip(kutu["boxes"], o.DONEMLER):
            parca.set_facecolor(RENK[p]); parca.set_alpha(0.6)
        r = ist.set_index("degisken").loc[d]
        ax.set_title(f"{d}\nε²={r.epsilon2:.3f}, p={r.p:.3g}", fontsize=8)
    for ax in np.ravel(eksenler)[len(degiskenler):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(o.GRAFIK / "kutu_grafikleri.png")
    plt.close(fig)
    return ist, ik


# ---------------------------------------------------------------------------
# 2) MODEL (H4)
# ---------------------------------------------------------------------------
def rf(agac=o.AGAC_SAYISI):
    return RandomForestClassifier(n_estimators=agac, class_weight="balanced", min_samples_leaf=3,
                                  random_state=o.RASTGELE, n_jobs=-1)


def capraz_dogrula(model_fn, X, y, gruplar=None, onem=False):
    """Katman katman eğitir/test eder. gruplar verilirse MEKÂNSAL blok doğrulama yapar."""
    if gruplar is not None:
        bolucu = StratifiedGroupKFold(n_splits=o.KATMAN_SAYISI, shuffle=True, random_state=o.RASTGELE)
        bolmeler = bolucu.split(X, y, gruplar)
    else:
        bolucu = StratifiedKFold(n_splits=o.KATMAN_SAYISI, shuffle=True, random_state=o.RASTGELE)
        bolmeler = bolucu.split(X, y)
    tahmin = np.empty(len(y), dtype=object)
    skorlar, onemler = [], []
    for egitim, test in bolmeler:
        m = model_fn().fit(X.iloc[egitim], y[egitim])
        tahmin[test] = m.predict(X.iloc[test])
        skorlar.append(balanced_accuracy_score(y[test], tahmin[test]))
        if onem:
            pi = permutation_importance(m, X.iloc[test], y[test], scoring="balanced_accuracy",
                                        n_repeats=o.PERMUTASYON_TEKRAR, random_state=o.RASTGELE, n_jobs=-1)
            onemler.append(pi.importances_mean)
    sonuc = {"dengeli_dogruluk_ort": float(np.mean(skorlar)),
             "dengeli_dogruluk_ss": float(np.std(skorlar)),
             "katman_skorlari": [float(s) for s in skorlar],
             "tahmin": tahmin}
    if onem:
        sonuc["onem"] = pd.Series(np.mean(onemler, axis=0), index=X.columns)
    return sonuc


def model_analizi(df, degiskenler):
    y = df["ilk_donem"].to_numpy()
    tum = degiskenler
    temiz = [d for d in degiskenler if d not in o.ONYARGI_DEGISKENLERI]
    metrik = {}

    # a) Ana model: önyargı değişkenleri HARİÇ, mekânsal doğrulama
    ana = capraz_dogrula(rf, df[temiz], y, df["blok"], onem=True)
    metrik["rf_mekansal"] = {k: v for k, v in ana.items() if k not in ("tahmin", "onem")}
    metrik["rf_mekansal"]["f1_sinif"] = dict(zip(o.DONEMLER, f1_score(y, ana["tahmin"], labels=o.DONEMLER, average=None).round(3).tolist()))
    km = confusion_matrix(y, ana["tahmin"], labels=o.DONEMLER)
    pd.DataFrame(km, index=[f"gercek_{d}" for d in o.DONEMLER],
                 columns=[f"tahmin_{d}" for d in o.DONEMLER]).to_csv(o.SONUC / "karmasiklik.csv")

    # b) Karşılaştırma: aynı model, RASTGELE doğrulama (şişkin doğruluğu göstermek için)
    rast = capraz_dogrula(rf, df[temiz], y)
    metrik["rf_rastgele"] = {k: v for k, v in rast.items() if k != "tahmin"}

    # c) Karşılaştırma: lojistik regresyon (Kalaycı 2006'nın yöntemi), mekânsal doğrulama
    lr = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, class_weight="balanced"))
    lr_s = capraz_dogrula(lr, df[temiz], y, df["blok"])
    metrik["lojistik_mekansal"] = {k: v for k, v in lr_s.items() if k != "tahmin"}

    # d) H4: Etiket karıştırma testi. Dönem etiketleri rastgele karıştırıldığında model
    #    ne kadar başarılı oluyor? Gerçek skor, karıştırılmışların %95'inden iyiyse anlamlı.
    skor, karisik, p = permutation_test_score(
        rf(200), df[temiz], y, groups=df["blok"],
        cv=StratifiedGroupKFold(n_splits=o.KATMAN_SAYISI, shuffle=True, random_state=o.RASTGELE),
        n_permutations=o.ETIKET_PERMUTASYON, scoring="balanced_accuracy",
        random_state=o.RASTGELE, n_jobs=-1)
    metrik["etiket_karistirma"] = {"gercek_skor": float(skor), "karisik_ort": float(karisik.mean()),
                                   "karisik_95": float(np.percentile(karisik, 95)), "p": float(p)}

    # e) H0: Önyargı değişkenleri DAHİL model
    onem = pd.DataFrame({"degisken": temiz, "tema": [o.TEMALAR[d] for d in temiz],
                         "onem_onyargi_haric": ana["onem"].reindex(temiz).to_numpy()})
    if len(tum) > len(temiz):
        dahil = capraz_dogrula(rf, df[tum], y, df["blok"], onem=True)
        metrik["rf_mekansal_onyargi_dahil"] = {k: v for k, v in dahil.items() if k not in ("tahmin", "onem")}
        onem = pd.DataFrame({"degisken": tum, "tema": [o.TEMALAR[d] for d in tum],
                             "onem_onyargi_dahil": dahil["onem"].reindex(tum).to_numpy()}).merge(
            onem.drop(columns="tema"), on="degisken", how="left")
    onem = onem.sort_values(onem.columns[2], ascending=False)
    onem.to_csv(o.SONUC / "onem.csv", index=False)

    # Grafik: permütasyon önemi
    sira = onem.sort_values("onem_onyargi_haric", na_position="first")
    fig, ax = plt.subplots(figsize=(6, 0.35 * len(sira) + 1))
    ax.barh(sira.degisken, sira.onem_onyargi_haric, color="#555")
    if "onem_onyargi_dahil" in sira:
        ax.scatter(sira.onem_onyargi_dahil, sira.degisken, color="#c0392b", zorder=3, label="önyargı değişkenleri dahil")
        ax.legend(loc="lower right")
    ax.set_xlabel("Permütasyon önemi (dengeli doğrulukta düşüş)")
    ax.set_title("Hangi değişken dönemi ayırt ediyor?")
    fig.tight_layout(); fig.savefig(o.GRAFIK / "onem.png"); plt.close(fig)

    # Grafik: karmaşıklık matrisi
    fig, ax = plt.subplots(figsize=(4, 3.5))
    ax.imshow(km, cmap="Greys")
    ax.set_xticks(range(3), o.DONEMLER); ax.set_yticks(range(3), o.DONEMLER)
    ax.set_xlabel("Tahmin"); ax.set_ylabel("Gerçek")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, km[i, j], ha="center", va="center", color="white" if km[i, j] > km.max() / 2 else "black")
    ax.set_title("Mekânsal doğrulama")
    fig.tight_layout(); fig.savefig(o.GRAFIK / "karmasiklik.png"); plt.close(fig)

    # Grafik: kısmi bağımlılık (bütün veriyle eğitilmiş modelden)
    son = rf().fit(df[temiz], y)
    for donem in o.DONEMLER:
        fig, ax = plt.subplots(figsize=(12, 2.6 * int(np.ceil(len(temiz) / 4))))
        PartialDependenceDisplay.from_estimator(son, df[temiz], temiz, target=donem, n_cols=4, ax=ax,
                                                grid_resolution=30, line_kw={"color": RENK[donem]})
        fig.suptitle(f"Kısmi bağımlılık: {donem} olasılığı", y=1.0)
        fig.tight_layout(); fig.savefig(o.GRAFIK / f"kismi_bagimlilik_{donem}.png"); plt.close(fig)

    return metrik, onem


# ---------------------------------------------------------------------------
# 3) KAYMA: İkili karşılaştırmalar (ana hipotez)
# ---------------------------------------------------------------------------
def kayma_analizi(df, degiskenler):
    temiz = [d for d in degiskenler if d not in o.ONYARGI_DEGISKENLERI]
    satirlar = []
    for a, b in [("Neolitik", "Kalkolitik"), ("Kalkolitik", "Tunc")]:
        alt = df[df.ilk_donem.isin([a, b])].reset_index(drop=True)
        s = capraz_dogrula(rf, alt[temiz], alt.ilk_donem.to_numpy(), alt.blok, onem=True)
        for d in temiz:
            satirlar.append({"karsilastirma": f"{a} → {b}", "degisken": d, "tema": o.TEMALAR[d],
                             "onem": s["onem"][d], "dengeli_dogruluk": s["dengeli_dogruluk_ort"]})
    k = pd.DataFrame(satirlar)
    k.to_csv(o.SONUC / "kayma.csv", index=False)

    tema = k.assign(onem=k.onem.clip(lower=0)).groupby(["karsilastirma", "tema"]).onem.sum().unstack(0)
    tema = tema[["Neolitik → Kalkolitik", "Kalkolitik → Tunc"]]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    tema.plot.bar(ax=ax, color=[RENK["Kalkolitik"], RENK["Tunc"]])
    ax.legend(title="Geçiş")
    ax.set_ylabel("Toplam permütasyon önemi"); ax.set_xlabel("")
    ax.set_title("Dönem geçişlerinde hangi tema ayırt edici?")
    plt.xticks(rotation=0)
    fig.tight_layout(); fig.savefig(o.GRAFIK / "kayma.png"); plt.close(fig)
    return k


# ---------------------------------------------------------------------------
# 4) DUYARLILIK ANALİZLERİ
# ---------------------------------------------------------------------------
def duyarlilik(df, degiskenler):
    temiz = [d for d in degiskenler if d not in o.ONYARGI_DEGISKENLERI]
    altlar = {"Tüm veri": df,
              "Sadece tek dönemli yerleşimler": df[df.tek_donemli.isin(["evet"])],
              "Sadece kesin koordinatlar (kesinlik=1)": df[df.koord_kesinlik == 1]}
    for kaynak in df.kaynak.unique():
        altlar[f"Sadece kaynak: {kaynak}"] = df[df.kaynak == kaynak]
    satirlar = []
    for ad, alt in altlar.items():
        sayim = alt.ilk_donem.value_counts().reindex(o.DONEMLER, fill_value=0)
        satir = {"analiz": ad, "n": len(alt), **{f"n_{d}": int(v) for d, v in sayim.items()}}
        if sayim.min() >= o.KATMAN_SAYISI * 2 and alt.blok.nunique() >= o.KATMAN_SAYISI:
            s = capraz_dogrula(rf, alt[temiz].reset_index(drop=True), alt.ilk_donem.to_numpy(),
                               alt.blok.reset_index(drop=True))
            satir["dengeli_dogruluk"] = s["dengeli_dogruluk_ort"]
        else:
            satir["dengeli_dogruluk"] = np.nan
            satir["not"] = "Yetersiz örnek; hesaplanmadı"
        satirlar.append(satir)
    t = pd.DataFrame(satirlar)
    t.to_csv(o.SONUC / "duyarlilik.csv", index=False)
    return t


# ---------------------------------------------------------------------------
# 5) HİPOTEZ KARARLARI
# ---------------------------------------------------------------------------
def hipotez_kararlari(ist, ikili, metrik, onem):
    ist = ist.set_index("degisken")
    satirlar = []
    for hip, kosullar in o.HIPOTEZLER.items():
        parcalar = []
        for d, a, b, yon in kosullar:
            if d not in ist.index:
                parcalar.append((False, f"{d}: değişken hesaplanmadı (katman eksik)"))
                continue
            r = ist.loc[d]
            ik = ikili[(ikili.degisken == d) & (ikili.donem_1.isin([a, b])) & (ikili.donem_2.isin([a, b]))].iloc[0]
            ma = ik.ortanca_1 if ik.donem_1 == a else ik.ortanca_2
            mb = ik.ortanca_2 if ik.donem_1 == a else ik.ortanca_1
            yon_ok = (ma < mb) if yon == "kucuk" else (ma > mb)
            ok = bool(r.p < o.ANLAMLILIK and r.epsilon2 >= o.ETKI_ESIGI and yon_ok and ik.p_bonferroni < o.ANLAMLILIK)
            parcalar.append((ok, f"{d}: {a} ortanca {ma:.3g} vs {b} {mb:.3g} "
                                 f"(beklenen: {'küçük' if yon == 'kucuk' else 'büyük'}), "
                                 f"ε²={r.epsilon2:.3f}, KW p={r.p:.3g}, çift p={ik.p_bonferroni:.3g}"))
        tum_ok = all(p[0] for p in parcalar)
        kismi = any(p[0] for p in parcalar)
        satirlar.append({"hipotez": hip,
                         "karar": "Destekleniyor" if tum_ok else ("Kısmen destekleniyor" if kismi else "Desteklenmiyor"),
                         "ayrinti": " | ".join(p[1] for p in parcalar)})

    s = metrik["rf_mekansal"]["dengeli_dogruluk_ort"]
    p = metrik["etiket_karistirma"]["p"]
    satirlar.append({"hipotez": "H4 Ayırt edilebilirlik",
                     "karar": "Destekleniyor" if (s >= o.H4_DOGRULUK_ESIGI and p < o.ANLAMLILIK) else "Desteklenmiyor",
                     "ayrinti": f"Mekânsal dengeli doğruluk {s:.3f} (eşik {o.H4_DOGRULUK_ESIGI}, şans 0.333); "
                                f"etiket karıştırma p={p:.3g}"})

    if "onem_onyargi_dahil" in onem:
        ilk2 = onem.sort_values("onem_onyargi_dahil", ascending=False).degisken.head(2).tolist()
        var = [d for d in o.ONYARGI_DEGISKENLERI if d in ilk2]
        satirlar.append({"hipotez": "H0 Önyargı",
                         "karar": "Destekleniyor (DİKKAT: veri araştırma önyargısı taşıyor)" if var else "Desteklenmiyor (önyargı baskın değil)",
                         "ayrinti": f"Önyargı dahil modelde en önemli 2 değişken: {ilk2}"})
    else:
        satirlar.append({"hipotez": "H0 Önyargı", "karar": "Test edilemedi",
                         "ayrinti": "yol_mesafe_m / koy_mesafe_m hesaplanmadı (OSM katmanı eksik)"})
    t = pd.DataFrame(satirlar)
    t.to_csv(o.SONUC / "hipotezler.csv", index=False)
    return t


# ---------------------------------------------------------------------------
def main():
    o.klasorleri_hazirla()
    df, degiskenler = veriyi_yukle()
    print(f"Kullanılan değişkenler ({len(degiskenler)}): {degiskenler}")
    print("Dönem sayıları:", df.ilk_donem.value_counts().reindex(o.DONEMLER).to_dict())

    print("\n[1/4] İstatistik testleri..."); ist, ik = istatistik(df, degiskenler)
    print("[2/4] Random Forest ve doğrulama (birkaç dakika sürebilir)..."); metrik, onem = model_analizi(df, degiskenler)
    print("[3/4] Kayma analizi..."); kayma_analizi(df, degiskenler)
    print("[4/4] Duyarlılık analizleri..."); duy = duyarlilik(df, degiskenler)
    hip = hipotez_kararlari(ist, ik, metrik, onem)

    metrik["calistirma"] = {"tarih": datetime.now().isoformat(timespec="seconds"),
                            "scikit_learn": sklearn.__version__, "rastgele_tohum": o.RASTGELE,
                            "blok_boyutu_m": o.BLOK_BOYUTU_M, "blok_sayisi": int(df.blok.nunique()),
                            "n": int(len(df)), "degiskenler": degiskenler,
                            "donem_sayilari": df.ilk_donem.value_counts().reindex(o.DONEMLER).astype(int).to_dict()}
    (o.SONUC / "model_metrikleri.json").write_text(json.dumps(metrik, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== SONUÇ ÖZETİ ===")
    print(f"RF mekânsal doğrulama : {metrik['rf_mekansal']['dengeli_dogruluk_ort']:.3f}")
    print(f"RF rastgele doğrulama : {metrik['rf_rastgele']['dengeli_dogruluk_ort']:.3f}  (fark = şişme payı)")
    print(f"Lojistik reg. mekânsal: {metrik['lojistik_mekansal']['dengeli_dogruluk_ort']:.3f}")
    print(f"Şans düzeyi           : 0.333")
    print(hip[["hipotez", "karar"]].to_string(index=False))
    print(f"\nBütün çıktılar: {o.SONUC}")


if __name__ == "__main__":
    main()
