"""Sonuç gösterim uygulaması (Streamlit).

Bu uygulama HİÇBİR hesaplama yapmaz ve HİÇBİR sayıyı kendi içinde barındırmaz.
Ekrandaki her değer, 01_degisken_hesapla.py ve 02_model.py'nin sonuclar/ klasörüne
yazdığı dosyalardan okunur. Bir dosya yoksa ilgili bölüm "henüz üretilmedi" der.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

SONUC = Path(__file__).resolve().parent / "sonuclar"
GRAFIK = SONUC / "grafikler"
DONEMLER = ["Neolitik", "Kalkolitik", "Tunc"]
DONEM_AD = {"Neolitik": "Neolitik", "Kalkolitik": "Kalkolitik", "Tunc": "Tunç Çağı"}
RENK = {"Neolitik": "#3a7d44", "Kalkolitik": "#c07a2c", "Tunc": "#6b4f9e"}

st.set_page_config(page_title="Anadolu'da Üç Çağın Yerleşim Seçimi", layout="wide")


def oku_csv(ad):
    yol = SONUC / ad
    return pd.read_csv(yol) if yol.exists() else None


def oku_json(ad):
    yol = SONUC / ad
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else None


def grafik(ad, aciklama=None):
    yol = GRAFIK / ad
    if yol.exists():
        st.image(str(yol), use_container_width=True)
        if aciklama:
            st.caption(aciklama)
    else:
        uretilmedi(ad)


def uretilmedi(ad):
    st.info(f"Bu sonuç henüz üretilmedi (`sonuclar/{ad}` bulunamadı). Önce analiz betiklerini çalıştırın.")


degiskenler = oku_csv("degiskenler.csv")
metrik = oku_json("model_metrikleri.json")

st.title("Anadolu'da Neolitik, Kalkolitik ve Tunç Çağı Yerleşim Seçimi")
st.markdown("Coğrafi değişkenler ve Random Forest ile dönemler arası karşılaştırma. "
            "Bu sayfadaki bütün sayılar, depodaki analiz betiklerinin ürettiği dosyalardan okunur.")
if metrik:
    c = metrik["calistirma"]
    st.caption(f"Son analiz: {c['tarih']} · n = {c['n']} yerleşim · scikit-learn {c['scikit_learn']} · "
               f"rastgele tohum {c['rastgele_tohum']}")

sekmeler = st.tabs(["Veri", "Dönem karşılaştırması", "Model", "Neyi öğrendi?",
                    "Hipotezler", "Sınırlılıklar ve etik"])

# ---------------------------------------------------------------- Veri
with sekmeler[0]:
    if degiskenler is None:
        uretilmedi("degiskenler.csv")
    else:
        sayim = degiskenler["ilk_donem"].value_counts().reindex(DONEMLER, fill_value=0)
        kol = st.columns(4)
        kol[0].metric("Toplam yerleşim", len(degiskenler))
        for i, d in enumerate(DONEMLER, 1):
            kol[i].metric(DONEM_AD[d], int(sayim[d]))
        st.markdown("**Kaynaklara göre dağılım**")
        st.dataframe(pd.crosstab(degiskenler["kaynak"], degiskenler["ilk_donem"]).reindex(columns=DONEMLER, fill_value=0))

        secim = st.multiselect("Haritada gösterilecek dönemler", DONEMLER, default=DONEMLER,
                               format_func=lambda d: DONEM_AD[d])
        harita = folium.Map(location=[degiskenler.lat.mean(), degiskenler.lon.mean()], zoom_start=6,
                            tiles="CartoDB positron")
        for _, r in degiskenler[degiskenler.ilk_donem.isin(secim)].iterrows():
            folium.CircleMarker([r.lat, r.lon], radius=4, color=RENK[r.ilk_donem], fill=True,
                                fill_opacity=0.8, weight=1,
                                tooltip=f"{r['ad']} · {DONEM_AD[r.ilk_donem]} · kaynak: {r['kaynak']}").add_to(harita)
        st_folium(harita, height=480, use_container_width=True, returned_objects=[])
        st.caption("Noktalar, yayımlanmış arkeolojik envanterlerdeki bilinen yerleşimlerdir. "
                   "Her yerleşimin kaynağı veri tablosundaki 'kaynak' ve 'kaynak_kayit' sütunlarındadır.")
        with st.expander("Veri tablosu"):
            st.dataframe(degiskenler, use_container_width=True)

# ---------------------------------------------------------------- Dönem karşılaştırması
with sekmeler[1]:
    ist = oku_csv("istatistik.csv")
    if ist is None:
        uretilmedi("istatistik.csv")
    else:
        st.markdown("Her değişken için Kruskal-Wallis testi. **ε²** etki büyüklüğüdür "
                    "(yaklaşık: 0,01 küçük · 0,06 orta · 0,14 büyük).")
        goster = ist.rename(columns={f"ortanca_{d}": f"Ortanca {DONEM_AD[d]}" for d in DONEMLER})
        st.dataframe(goster.round({"H": 2, "epsilon2": 3, **{f"Ortanca {DONEM_AD[d]}": 1 for d in DONEMLER}}),
                     use_container_width=True)
        grafik("kutu_grafikleri.png")
        ik = oku_csv("ikili_testler.csv")
        if ik is not None:
            with st.expander("İkili karşılaştırmalar (Mann-Whitney U, Bonferroni düzeltmeli)"):
                st.dataframe(ik, use_container_width=True)

# ---------------------------------------------------------------- Model
with sekmeler[2]:
    if metrik is None:
        uretilmedi("model_metrikleri.json")
    else:
        st.markdown("**Dengeli doğruluk** (şans düzeyi: 0,333). Mekânsal doğrulamada model, "
                    "eğitimde hiç görmediği coğrafi bloklarda test edilir.")
        kol = st.columns(4)
        kol[0].metric("Random Forest · mekânsal", f"{metrik['rf_mekansal']['dengeli_dogruluk_ort']:.3f}",
                      help="Raporlanması gereken asıl sonuç")
        kol[1].metric("Random Forest · rastgele", f"{metrik['rf_rastgele']['dengeli_dogruluk_ort']:.3f}",
                      help="Komşu yerleşimler hem eğitimde hem testte olduğu için genellikle şişkindir")
        kol[2].metric("Lojistik regresyon · mekânsal", f"{metrik['lojistik_mekansal']['dengeli_dogruluk_ort']:.3f}")
        e = metrik["etiket_karistirma"]
        kol[3].metric("Etiket karıştırma testi p", f"{e['p']:.3g}",
                      help=f"Etiketler karıştırıldığında ortalama skor {e['karisik_ort']:.3f}")
        c1, c2 = st.columns(2)
        with c1:
            grafik("karmasiklik.png", "Satırlar gerçek dönem, sütunlar modelin tahmini.")
        with c2:
            st.markdown("**Sınıf başına F1**")
            st.dataframe(pd.Series(metrik["rf_mekansal"]["f1_sinif"], name="F1"))
            duy = oku_csv("duyarlilik.csv")
            st.markdown("**Duyarlılık analizleri**")
            if duy is not None:
                st.dataframe(duy.round(3), use_container_width=True)
            else:
                uretilmedi("duyarlilik.csv")

# ---------------------------------------------------------------- Neyi öğrendi?
with sekmeler[3]:
    st.markdown("**Permütasyon önemi:** Bir değişkenin değerleri karıştırıldığında modelin başarısı ne kadar düşüyor? "
                "Kırmızı noktalar, modern yol ve köy mesafesi (araştırma önyargısı) modele eklendiğindeki durumu gösterir.")
    grafik("onem.png")
    st.markdown("**Dönem geçişleri:** Neolitik→Kalkolitik ve Kalkolitik→Tunç ayrımında hangi tema öne çıkıyor?")
    grafik("kayma.png")
    donem = st.selectbox("Kısmi bağımlılık grafiği", DONEMLER, format_func=lambda d: DONEM_AD[d])
    grafik(f"kismi_bagimlilik_{donem}.png",
           "Diğer değişkenler sabitken, bir değişken değiştikçe bu döneme ait olma olasılığı nasıl değişiyor?")

# ---------------------------------------------------------------- Hipotezler
with sekmeler[4]:
    hip = oku_csv("hipotezler.csv")
    if hip is None:
        uretilmedi("hipotezler.csv")
    else:
        st.markdown("Hipotezler ve eşikler analizden **önce** `ON_KAYIT.md` dosyasına yazılıp kaydedilmiştir.")
        for _, r in hip.iterrows():
            simge = "✅" if r.karar.startswith("Destekleniyor") else ("🟡" if r.karar.startswith("Kısmen") else "⬜")
            st.markdown(f"#### {simge} {r.hipotez}: {r.karar}")
            st.caption(r.ayrinti)

# ---------------------------------------------------------------- Sınırlılıklar
with sekmeler[5]:
    st.markdown("""
- **Modern coğrafya:** Akarsu ve yükseklik verileri bugünün haritalarından alınmıştır. Akarsular yatak değiştirmiş, ovalar alüvyonla dolmuş olabilir.
- **Araştırma önyargısı:** Yerleşimler, arkeologların araştırma yaptığı yerlerde bilinir. Bu etki, modern yol ve köy mesafesiyle ayrıca ölçülmüştür (bkz. H0).
- **Dönem etiketleri:** Birçok yerleşimin dönemi yüzey buluntularına dayanır. Hedef değişken, yerleşimin ilk iskân edildiği dönemdir.
- **Veri kaynakları:** Dönemler farklı envanterlerden geliyorsa fark kısmen kaynak farkından doğabilir; bu, duyarlılık analizinde tek kaynakla tekrar edilerek kontrol edilmiştir.
- **Etik:** Bu uygulama "henüz kazılmamış aday yerleşim" koordinatı göstermez. Ayrıntılı tahmin haritaları kaçak kazıya yol gösterebileceği için (2863 sayılı Kanun) yayımlanmamıştır.
""")
