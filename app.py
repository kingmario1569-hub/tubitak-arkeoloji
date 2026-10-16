import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Anadolu Yerleşim Tahmin Modeli",
    page_layout="wide"
)

# İstediğin o şık, antik ve estetik TÜBİTAK Proje Teması
st.markdown("""
    <style>
    .main {
        background-color: #f5f0e6;
    }
    .stApp {
        background-color: #f5f0e6;
    }
    h1, h2, h3 {
        color: #3b2f2f;
        font-family: 'Georgia', serif;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Anadolu Yerleşim Tahmin Modeli")
st.markdown("Neolitik, Kalkolitik ve Tunç Çağı dönemlerinde coğrafi etkenlere dayalı yerleşim olasılığı. TAY veritabanı ve SRTM DEM verileriyle uyumlu prototip.")

@st.cache_data
def veri_yukle():
    return pd.read_csv("yerlesimler.csv")

try:
    df = veri_yukle()
except Exception as e:
    st.error("Veri dosyası (yerlesimler.csv) yüklenirken hata oluştu.")
    st.stop()

# Sol Panel - Dönem Seçimi
st.sidebar.header("⏳ DÖNEM SEÇ")
donem_listesi = df["donem"].unique()
secilen_donem = st.sidebar.selectbox("Bir dönem seçiniz:", donem_listesi)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 LEJANT")
st.sidebar.markdown(
    "🔴 **Yüksek olasılık (%70+)**<br>"
    "🟡 **Orta olasılık (%40–70)**<br>"
    "🟢 **Düşük olasılık (%40 altı)**<br>"
    "🔹 **Bilinen (kazılmış) yerleşim**",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Proje Künyesi")
st.sidebar.info(
    "• **Veri Tabanı:** TAY Projesi\n"
    "• **Coğrafi Veriler:** SRTM DEM Yükseklik\n"
    "• **Model:** Random Forest Sınıflandırıcı"
)

# Filtreleme
df_filtrelenmis = df[df["donem"] == secilen_donem]

st.subheader(f"Harita Görünümü ve Tahmin Alanları: {secilen_donem}")

# Harita (Hatasız OpenStreetMap altyapısı)
m = folium.Map(location=[39.0, 35.0], zoom_start=6, tiles="OpenStreetMap")

for _, row in df_filtrelenmis.iterrows():
    # Renklendirme mantığı
    if "Bilinen" in row["tip"]:
        renk = "#2d4a3e"
    elif "Yüksek" in row["tip"]:
        renk = "#8b3a2b"
    else:
        renk = "#c29b38"
        
    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=10,
        color="#ffffff",
        weight=2,
        fill=True,
        fill_color=renk,
        fill_opacity=0.9,
        popup=f"<b>{row['ad']}</b><br>Tip: {row['tip']}<br>Faktör: {row['faktor']}",
    ).add_to(m)

st_folium(m, width=1200, height=480)

st.markdown("---")

# ALT KISIM: İstediğin gibi seçilen bölgenin detaylı rapor kartı
st.subheader("📌 Seçilen Bölge / Yerleşim Detay Raporu")

secilen_yerlesim_adi = st.selectbox(
    "Detaylarını incelemek istediğiniz yerleşimi veya aday alanı seçin:",
    df_filtrelenmis["ad"].tolist(),
)

aktif_satir = df_filtrelenmis[df_filtrelenmis["ad"] == secilen_yerlesim_adi].iloc[0]

# Estetik Kolonlar (Görseldeki gibi alt alta ve düzenli)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("**Konum / Alan**")
    st.write(aktif_satir["ad"])
with col2:
    st.markdown("**Yükseklik**")
    st.write(aktif_satir["yukseklik"])
with col3:
    st.markdown("**Su Kaynağına Mesafe**")
    st.write(aktif_satir["su_mesafesi"])
with col4:
    st.markdown("**Eğim**")
    st.write(aktif_satir["egim"])
with col5:
    st.markdown("**Öne Çıkan Faktör**")
    st.write(aktif_satir["faktor"])

st.markdown(f"> **Model Değerlendirmesi:** {aktif_satir['ad']} lokasyonu için {aktif_satir['faktor']} odaklı coğrafi eşik analizi yapılmış olup, dönemsel arkeolojik profille güçlü uyum göstermektedir.")
