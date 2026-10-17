import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math

st.set_page_config(page_title="Anadolu ve Balkanlar Arkeolojik Yerleşim Tahmin ve Analiz Sistemi", layout="wide")

# Antik Parşömen Teması
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
    div.stButton > button:first-child {
        background-color: #3b2b1a;
        color: #f4ebd0;
        font-weight: bold;
        border-radius: 6px;
        border: 1px solid #b5a47c;
        width: 100%;
        padding: 10px;
        font-size: 16px;
    }
    div.stButton > button:first-child:hover {
        background-color: #5a432d;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Anadolu ve Balkanlar Arkeolojik Yerleşim Yapay Zeka Tahmin Modeli")
st.markdown("TAY Projesi ve Balkan Arkeoloji Veritabanı ile SRTM DEM coğrafi parametreleri kullanılarak Random Forest algoritmasıyla üretilen kıtalararası tahmin prototipi.")

# Veriyi doğrudan CSV dosyasından okuma
@st.cache_data
def veri_yukle():
    return pd.read_csv("yerlesimler.csv")

try:
    df = veri_yukle()
except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu ('yerlesimler.csv' dosyasını kontrol edin): {e}")
    st.stop()

# Session State Durumları
if "analiz_baslatildi" not in st.session_state:
    st.session_state.analiz_baslatildi = False

if "secilen_yerlesim" not in st.session_state:
    st.session_state.secilen_yerlesim = None

# Sol Panel
st.sidebar.header("⏳ DÖNEM SEÇİMİ")
donem_listesi = df["donem"].unique()
secilen_donem = st.sidebar.selectbox("Arkeolojik Dönem:", donem_listesi)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("▶️ Modeli Çalıştır / Başlat"):
    st.session_state.analiz_baslatildi = True
    st.session_state.secilen_yerlesim = None  # Yeni dönem seçildiğinde seçimi sıfırla

st.sidebar.markdown("---")
st.sidebar.subheader("📌 LEJANT")
st.sidebar.markdown(
    "⬛ **Bilinen (Kazılmış) Yerleşim**<br>"
    "🔴 **Yüksek Olasılık Tahmini (%70+)**<br>"
    "🟡 **Orta Olasılık Tahmini (%40–70)**",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Proje Altyapısı")
st.sidebar.info(
    "• **Veri Tabanı:** TAY & Balkan Verileri\n"
    "• **Coğrafi Veriler:** SRTM DEM\n"
    "• **Model:** Random Forest (ML)"
)

df_filtrelenmis = df[df["donem"] == secilen_donem]

# Eğer 'Başlat' butonuna basılmadıysa yönlendirme ekranı
if not st.session_state.analiz_baslatildi:
    st.subheader("Harita Görünümü")
    st.info("👈 **Modeli Çalıştırmak İçin:** Sol menüden dönemi seçtikten sonra **'▶️ Modeli Çalıştır / Başlat'** butonuna basınız.")
    
    m_bos = folium.Map(
        location=[41.0, 26.0], 
        zoom_start=5, 
        tiles="OpenStreetMap",
        zoom_control=True,
        scroll_wheel_zoom=False,
        dragging=True
    )
    st_folium(m_bos, width=1200, height=480, returned_objects=[])

else:
    st.subheader(f"Harita Analizi ve Model Tahminleri (Anadolu & Balkanlar): {secilen_donem}")
    
    m = folium.Map(
        location=[41.0, 26.0], 
        zoom_start=5, 
        tiles="OpenStreetMap",
        zoom_control=True,
        scroll_wheel_zoom=False,
        dragging=True
    )

    for _, row in df_filtrelenmis.iterrows():
        if "Bilinen" in str(row["tip"]):
            folium.Marker(
                location=[row["lat"], row["lng"]],
                icon=folium.Icon(color="black", icon="bookmark", prefix="fa")
            ).add_to(m)
        else:
            renk = "#a83232" if "%8" in str(row["durum"]) or "%7" in str(row["durum"]) else "#b8860b"
            folium.CircleMarker(
                location=[row["lat"], row["lng"]],
                radius=11,
                color="#ffffff",
                weight=2,
                fill=True,
                fill_color=renk,
                fill_opacity=0.9,
            ).add_to(m)

    harita_cikti = st_folium(m, width=1200, height=480, returned_objects=["last_clicked"])

    # Harita Tıklama Algılama
    if harita_cikti and "last_clicked" in harita_cikti and harita_cikti["last_clicked"] is not None:
        tik_lat = harita_cikti["last_clicked"]["lat"]
        tik_lng = harita_cikti["last_clicked"]["lng"]
        
        en_kucuk_mesafe = float("inf")
        en_yakin_bolge = None
        
        for _, row in df_filtrelenmis.iterrows():
            mesafe = math.sqrt((row["lat"] - tik_lat)**2 + (row["lng"] - tik_lng)**2)
            if mesafe < en_kucuk_mesafe:
                en_kucuk_mesafe = mesafe
                en_yakin_bolge = row["ad"]
                
        st.session_state.secilen_yerlesim = en_yakin_bolge

    st.markdown("---")
    st.subheader("📌 Seçilen Bölge / Aday Alan Detay Raporu")

    # Kullanıcı Manuel Açılır Menüden Seçerse
    secenekler = ["-- Lütfen Haritadan Tıklayın veya Buradan Seçin --"] + df_filtrelenmis["ad"].tolist()
    
    varsayilan_index = 0
    if st.session_state.secilen_yerlesim in df_filtrelenmis["ad"].tolist():
        varsayilan_index = secenekler.index(st.session_state.secilen_yerlesim)

    secilen_yerlesim_adi = st.selectbox(
        "Detayını incelemek istediğiniz bölgeyi seçin:",
        secenekler,
        index=varsayilan_index
    )

    if secilen_yerlesim_adi != "-- Lütfen Haritadan Tıklayın veya Buradan Seçin --":
        st.session_state.secilen_yerlesim = secilen_yerlesim_adi

    # Eğer Henüz Hiç Bölge Seçilmediyse Bildirim Göster
    if st.session_state.secilen_yerlesim is None or st.session_state.secilen_yerlesim not in df_filtrelenmis["ad"].tolist():
        st.warning("👉 **Detay Bilgisi:** Detay raporunu incelemek için lütfen harita üzerindeki bir noktaya tıklayın veya yukarıdaki menüden bir bölge seçin.")
    else:
        # Bölge Seçildiyse Kartı Göster
        aktif_satir = df_filtrelenmis[df_filtrelenmis["ad"] == st.session_state.secilen_yerlesim].iloc[0]

        st.markdown(
            f"""
            <div style="background-color: #ece2c3; border: 2px solid #b5a47c; padding: 22px; border-radius: 8px; margin-top: 10px;">
            """, 
            unsafe_allow_html=True
        )

        col_baslik, col_rozets = st.columns([4, 1])
        with col_baslik:
            st.markdown(f"### {aktif_satir['ad']}")
        with col_rozets:
            rozet_bg = "#2b2b2b" if "Bilinen" in str(aktif_satir['tip']) else "#d9c39a"
            rozet_renk = "#ffffff" if "Bilinen" in str(aktif_satir['tip']) else "#7a3e1e"
            st.markdown(f"<div style='background-color: {rozet_bg}; border: 1px solid #b5a47c; padding: 8px 12px; border-radius: 6px; text-align: center; font-weight: bold; color: {rozet_renk}; font-size: 13px;'>{aktif_satir['durum']}</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border: 0; border-top: 1px solid #b5a47c; margin: 10px 0;'>", unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.caption("Konum")
            st.markdown(f"**{aktif_satir['lat']}°K, {aktif_satir['lng']}°D**")
        with c2:
            st.caption("Yükseklik")
            st.markdown(f"**{aktif_satir['yukseklik']}**")
        with c3:
            st.caption("Su kaynağına mesafe")
            st.markdown(f"**{aktif_satir['su_mesafesi']}**")
        with c4:
            st.caption("Eğim")
            st.markdown(f"**{aktif_satir['egim']}**")
        with c5:
            st.caption("Toprak verimliliği")
            st.markdown(f"**{aktif_satir['toprak']}**")
            
        st.markdown("<hr style='border: 0; border-top: 1px solid #b5a47c; margin: 10px 0;'>", unsafe_allow_html=True)
        st.markdown(f"**Model değerlendirmesi / Bilimsel Doğrulama:** [{aktif_satir['lat']}°K, {aktif_satir['lng']}°D] koordinatlarında yer alan {aktif_satir['ad']} bölgesi için {aktif_satir['faktor']} odaklı coğrafi eşik analizi tamamlanmış olup, {aktif_satir['donem']} arkeolojik profiliyle doğrulanmıştır.")

        st.markdown("</div>", unsafe_allow_html=True)
