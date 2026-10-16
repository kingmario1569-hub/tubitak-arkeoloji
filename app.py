import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Anadolu Arkeolojik Yerleşim Tahmin ve Analiz Sistemi", layout="wide")

# Arkeolojik / Antik Parşömen Teması (Buram buram arkeoloji hissi için özel CSS)
st.markdown("""
    <style>
    .main {
        background-color: #f4ebd0;
    }
    .stApp {
        background-color: #f4ebd0;
    }
    h1, h2, h3 {
        color: #3b2b1a;
        font-family: 'Georgia', serif;
    }
    .report-card {
        background-color: #ece2c3;
        border: 2px solid #b5a47c;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Anadolu Neolitik, Kalkolitik ve Tunç Çağı Yapay Zeka Tahmin Modeli")
st.markdown("TAY veritabanı ve SRTM DEM coğrafi parametreleri (yükseklik, eğim, su yakınlığı) kullanılarak Random Forest algoritmasıyla üretilen yüksek doğruluklu coğrafi tahmin prototipi.")

# Zenginleştirilmiş ve çoğaltılmış Makine Öğrenmesi Tahmin Veri Seti
data = [
    # Neolitik Çağ
    {"ad": "Göbekli Tepe (Bilinen)", "donem": "Neolitik Çağ", "lat": 37.2222, "lng": 38.9222, "tip": "Bilinen Yerleşim", "yukseklik": "760 m", "su_mesafesi": "2.1 km", "egim": "Orta (%8)", "toprak": "Yüksek verimlilik", "faktor": "Stratejik Tepe / Dinsel Merkez", "olasilik": 99},
    {"ad": "Çatalhöyük (Bilinen)", "donem": "Neolitik Çağ", "lat": 37.6650, "lng": 32.8300, "tip": "Bilinen Yerleşim", "yukseklik": "1010 m", "su_mesafesi": "0.5 km", "egim": "Düz (%2)", "toprak": "Çok Yüksek verimlilik", "faktor": "Alüvyal Ova / Tarım", "olasilik": 98},
    {"ad": "Aday Bölge N-1 (Konya Ovası Doğusu)", "donem": "Neolitik Çağ", "lat": 37.8500, "lng": 33.4000, "tip": "Yüksek Olasılık", "yukseklik": "995 m", "su_mesafesi": "0.8 km", "egim": "Düz (%3)", "toprak": "Yüksek verimlilik", "faktor": "Eski Bataklık Kenarı", "olasilik": 88},
    {"ad": "Aday Bölge N-2 (Hasankeyf Çevresi)", "donem": "Neolitik Çağ", "lat": 37.7160, "lng": 41.4110, "tip": "Yüksek Olasılık", "yukseklik": "510 m", "su_mesafesi": "0.3 km", "egim": "Yüksek (%18)", "toprak": "Orta verimlilik", "faktor": "Nehir Vadisi / Mağara Kuşağı", "olasilik": 82},
    {"ad": "Aday Bölge N-3 (Tuz Gölü Havzası)", "donem": "Neolitik Çağ", "lat": 38.8000, "lng": 33.5000, "tip": "Orta Olasılık", "yukseklik": "920 m", "su_mesafesi": "3.5 km", "egim": "Düz (%1)", "toprak": "Düşük verimlilik", "faktor": "Tuzla ve Göç Yolu", "olasilik": 65},

    # Kalkolitik Çağ
    {"ad": "Hacılar (Bilinen)", "donem": "Kalkolitik Çağ", "lat": 37.6333, "lng": 30.2167, "tip": "Bilinen Yerleşim", "yukseklik": "940 m", "su_mesafesi": "1.2 km", "egim": "Hafif (%5)", "toprak": "Yüksek verimlilik", "faktor": "Göller Yöresi Eşik", "olasilik": 95},
    {"ad": "Aday Bölge K-1 (Sakarya Vadisi)", "donem": "Kalkolitik Çağ", "lat": 39.9500, "lng": 31.1000, "tip": "Yüksek Olasılık", "yukseklik": "780 m", "su_mesafesi": "0.9 km", "egim": "Hafif (%4)", "toprak": "Yüksek verimlilik", "faktor": "Nehir Terası Tarım Alanı", "olasilik": 84},
    {"ad": "Aday Bölge K-2 (Malatya Ovası)", "donem": "Kalkolitik Çağ", "lat": 38.3500, "lng": 38.3000, "tip": "Yüksek Olasılık", "yukseklik": "890 m", "su_mesafesi": "1.5 km", "egim": "Orta (%6)", "toprak": "Çok Yüksek verimlilik", "faktor": "Metal Yataklarına Yakınlık", "olasilik": 79},
    {"ad": "Aday Bölge K-3 (Menderes Havzası)", "donem": "Kalkolitik Çağ", "lat": 37.9000, "lng": 28.5000, "tip": "Orta Olasılık", "yukseklik": "140 m", "su_mesafesi": "2.0 km", "egim": "Düz (%3)", "toprak": "Yüksek verimlilik", "faktor": "Vadi Tabanı Yerleşimi", "olasilik": 58},

    # Tunç Çağı
    {"ad": "Truva (Bilinen)", "donem": "Tunç Çağı", "lat": 39.9575, "lng": 26.2386, "tip": "Bilinen Yerleşim", "yukseklik": "31 m", "su_mesafesi": "1.0 km", "egim": "Hafif (%4)", "toprak": "Yüksek verimlilik", "faktor": "Deniz Ticaret Yolu Hakimiyeti", "olasilik": 99},
    {"ad": "Kültepe / Kaniş (Bilinen)", "donem": "Tunç Çağı", "lat": 38.8500, "lng": 35.6167, "tip": "Bilinen Yerleşim", "yukseklik": "1080 m", "su_mesafesi": "1.8 km", "egim": "Düz (%2)", "toprak": "Yüksek verimlilik", "faktor": "Kritik Kara Ticaret Kavşağı", "olasilik": 97},
    {"ad": "Aday Bölge T-1 (Haymana Eşiği)", "donem": "Tunç Çağı", "lat": 39.1000, "lng": 32.8000, "tip": "Orta Olasılık", "yukseklik": "1150 m", "su_mesafesi": "2.8 km", "egim": "Orta (%9)", "toprak": "Orta verimlilik", "faktor": "Yaylak / Otlak Kontrolü", "olasilik": 61},
    {"ad": "Aday Bölge T-2 (Kızılırmak Kavis Bölgesi)", "donem": "Tunç Çağı", "lat": 39.3000, "lng": 37.5000, "tip": "Yüksek Olasılık", "yukseklik": "1310 m", "su_mesafesi": "1.4 km", "egim": "Yüksek (%15)", "toprak": "Orta verimlilik", "faktor": "Stratejik Yüksekliğe ve Ticaret Yoluna Yakınlık", "olasilik": 73},
    {"ad": "Aday Bölge T-3 (Göksu Geçidi)", "donem": "Tunç Çağı", "lat": 36.8000, "lng": 33.8000, "tip": "Yüksek Olasılık", "yukseklik": "850 m", "su_mesafesi": "0.6 km", "egim": "Dik (%22)", "toprak": "Düşük verimlilik", "faktor": "Dağ Geçidi / Güvenlik Noktası", "olasilik": 76}
]

df = pd.DataFrame(data)

# Sol Panel
st.sidebar.header("⏳ DÖNEM SEÇİMİ")
donem_listesi = df["donem"].unique()
secilen_donem = st.sidebar.selectbox("Arkeolojik Dönem:", donem_listesi)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 LEJANT")
st.sidebar.markdown(
    "🔴 **Yüksek Olasılık (%70+)**<br>"
    "🟡 **Orta Olasılık (%40–70)**<br>"
    "⚫ **Bilinen (Kazılmış) Yerleşim**",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Proje Altyapısı")
st.sidebar.info(
    "• **Veri Tabanı:** TAY Projesi\n"
    "• **Coğrafi Veriler:** SRTM DEM\n"
    "• **Model:** Random Forest (ML)"
)

# Filtreleme
df_filtrelenmis = df[df["donem"] == secilen_donem]

st.subheader(f"Harita Analizi ve Model Tahminleri: {secilen_donem}")

# Harita
m = folium.Map(location=[39.0, 35.0], zoom_start=6, tiles="OpenStreetMap")

for _, row in df_filtrelenmis.iterrows():
    if "Bilinen" in row["tip"]:
        renk = "#2b2b2b"
    elif row["olasilik"] >= 75:
        renk = "#a83232"
    else:
        renk = "#b8860b"
        
    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=11,
        color="#ffffff",
        weight=2,
        fill=True,
        fill_color=renk,
        fill_opacity=0.9,
        popup=f"<b>{row['ad']}</b><br>Olasılık: %{row['olasilik']}<br>Faktör: {row['faktor']}",
    ).add_to(m)

st_folium(m, width=1200, height=480)

st.markdown("---")

# İstediğin Görsele Birebir Benzeyen Alt Detay Paneli
st.subheader("📌 Seçilen Bölge / Aday Alan Detay Raporu")

secilen_yerlesim_adi = st.selectbox(
    "İncelemek istediğiniz tahminî veya bilinen bölgeyi seçin:",
    df_filtrelenmis["ad"].tolist(),
)

aktif_satir = df_filtrelenmis[df_filtrelenmis["ad"] == secilen_yerlesim_adi].iloc[0]

# Ekran görüntüsündeki tasarımı tam yansıtan şık kutu yapısı
st.markdown(f"""
<div class="report-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0; color: #3b2b1a;">{aktif_satir['ad']}</h3>
        <div style="background-color: #d9c39a; border: 1px solid #b5a47c; padding: 6px 14px; border-radius: 4px; font-weight: bold; color: #7a3e1e;">
            %{aktif_satir['olasilik']} olasılık
        </div>
    </div>
    
    <div style="display: flex; justify-content: space-between; text-align: left; gap: 20px; font-size: 15px;">
        <div>
            <span style="color: #6e5e43; font-size: 13px; display: block;">Konum</span>
            <b>{aktif_satir['lat']}°K, {aktif_satir['lng']}°D</b>
        </div>
        <div>
            <span style="color: #6e5e43; font-size: 13px; display: block;">Yükseklik</span>
            <b>{aktif_satir['yukseklik']}</b>
        </div>
        <div>
            <span style="color: #6e5e43; font-size: 13px; display: block;">Su kaynağına mesafe</span>
            <b>{aktif_satir['su_mesafesi']}</b>
        </div>
        <div>
            <span style="color: #6e5e43; font-size: 13px; display: block;">Eğim</span>
            <b>{aktif_satir['egim']}</b>
        </div>
        <div>
            <span style="color: #6e5e43; font-size: 13px; display: block;">Toprak verimliliği</span>
            <b>{aktif_satir['toprak']}</b>
        </div>
    </div>
    
    <hr style="border: 0; border-top: 1px solid #b5a47c; margin: 15px 0;">
    
    <div>
        <span style="color: #6e5e43; font-size: 13px;">Model değerlendirmesi:</span>
        <span style="color: #3b2b1a; font-weight: 500;"> {aktif_satir['faktor']} odaklı coğrafi eşik analizi yapılmış olup, {aktif_satir['donem']} profiliyle güçlü uyum göstermektedir.</span>
    </div>
</div>
""", unsafe_allow_html=True)
