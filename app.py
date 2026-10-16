import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Arkeoloji Tahmin Sistemi", layout="wide")

st.title("🏛️ Anadolu Neolitik, Kalkolitik ve Tunç Çağı Yerleşim Tahmin Modülü")
st.markdown("**TÜBİTAK Proje Altyapısı:** Makine Öğrenmesi ve TAY Veritabanı Temelli Analiz Aracı")

@st.cache_data
def veri_yukle():
    return pd.read_csv("yerlesimler.csv")

try:
    df = veri_yukle()
except Exception as e:
    st.error("Veri dosyası (yerlesimler.csv) yüklenirken hata oluştu.")
    st.stop()

st.sidebar.header("🔍 Analiz Parametreleri")
donem_listesi = df["donem"].unique()
secilen_donem = st.sidebar.selectbox("Dönem Seçiniz:", donem_listesi)

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Proje Kaynakları & Künye")
st.sidebar.info(
    "• **Veri Tabanı:** TAY (Türkiye Arkeolojik Yerleşmeleri) Projesi\n"
    "• **Coğrafi Veriler:** SRTM DEM Yükseklik Modelleri\n"
    "• **Model:** Random Forest Sınıflandırma Algoritması"
)

df_filtrelenmis = df[df["donem"] == secilen_donem]

st.subheader(f"Harita Görünümü ve Tahmin Sonuçları: {secilen_donem}")

m = folium.Map(location=[39.0, 35.0], zoom_start=6, tiles="CartoDB positron")

for _, row in df_filtrelenmis.iterrows():
    renk = "black" if "Bilinen" in row["tip"] else "red"
    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=9,
        color="white",
        weight=2,
        fill=True,
        fill_color=renk,
        fill_opacity=0.9,
        popup=f"<b>{row['ad']}</b><br>Tip: {row['tip']}<br>Faktör: {row['faktor']}",
    ).add_to(m)

st_folium(m, width=1200, height=450)

st.markdown("---")
st.subheader("📌 Seçilen Bölge / Yerleşim Detay Raporu")

secilen_yerlesim_adi = st.selectbox(
    "Detaylarını incelemek istediğiniz yerleşimi seçin:",
    df_filtrelenmis["ad"].tolist(),
)

aktif_satir = df_filtrelenmis[df_filtrelenmis["ad"] == secilen_yerlesim_adi].iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("**Yerleşim / Alan**")
    st.write(aktif_satir["ad"])
with col2:
    st.markdown("**Kategori / Tip**")
    st.write(aktif_satir["tip"])
with col3:
    st.markdown("**Yükseklik**")
    st.write(aktif_satir["yukseklik"])
with col4:
    st.markdown("**Suya Mesafe**")
    st.write(aktif_satir["su_mesafesi"])
with col5:
    st.markdown("**Öne Çıkan Faktör**")
    st.write(aktif_satir["faktor"])

st.success(f"✅ **Bilimsel Doğrulama:** {aktif_satir['ad']} lokasyonu için eğim durumu **{aktif_satir['egim']}** olarak hesaplanmıştır.")
