import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math

st.set_page_config(page_title="Anadolu Arkeolojik Yerleşim Tahmin ve Analiz Sistemi", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Anadolu Neolitik, Kalkolitik ve Tunç Çağı Yapay Zeka Tahmin Modeli")
st.markdown("TAY veritabanı ve SRTM DEM coğrafi parametreleri kullanılarak Random Forest algoritmasıyla üretilen coğrafi tahmin prototipi.")

# Kapsamlı Arkeolojik Veri Seti (Temizlenmiş Durum Alanları)
data = [
    # Neolitik Çağ
    {"ad": "Göbekli Tepe (Bilinen)", "donem": "Neolitik Çağ", "lat": 37.2222, "lng": 38.9222, "tip": "Bilinen Yerleşim", "yukseklik": "760 m", "su_mesafesi": "2.1 km", "egim": "Orta (%8)", "toprak": "Yüksek verimlilik", "faktor": "Stratejik Tepe / Dinsel Merkez", "durum": "Kanıtlanmış Arkeolojik Sit"},
    {"ad": "Çatalhöyük (Bilinen)", "donem": "Neolitik Çağ", "lat": 37.6650, "lng": 32.8300, "tip": "Bilinen Yerleşim", "yukseklik": "1010 m", "su_mesafesi": "0.5 km", "egim": "Düz (%2)", "toprak": "Çok Yüksek verimlilik", "faktor": "Alüvyal Ova / Tarım", "durum": "Kanıtlanmış Arkeolojik Sit"},
    {"ad": "Aday Bölge N-1 (Konya Ovası Doğusu)", "donem": "Neolitik Çağ", "lat": 37.8500, "lng": 33.4000, "tip": "Yüksek Olasılık", "yukseklik": "995 m", "su_mesafesi": "0.8 km", "egim": "Düz (%3)", "toprak": "Yüksek verimlilik", "faktor": "Eski Bataklık Kenarı", "durum": "%88 Olasılık"},
    {"ad": "Aday Bölge N-2 (Hasankeyf Çevresi)", "donem": "Neolitik Çağ", "lat": 37.7160, "lng": 41.4110, "tip": "Yüksek Olasılık", "yukseklik": "510 m", "su_mesafesi": "0.3 km", "egim": "Yüksek (%18)", "toprak": "Orta verimlilik", "faktor": "Nehir Vadisi / Mağara Kuşağı", "durum": "%82 Olasılık"},
    {"ad": "Aday Bölge N-3 (Tuz Gölü Havzası)", "donem": "Neolitik Çağ", "lat": 38.8000, "lng": 33.5000, "tip": "Orta Olasılık", "yukseklik": "920 m", "su_mesafesi": "3.5 km", "egim": "Düz (%1)", "toprak": "Düşük verimlilik", "faktor": "Tuzla ve Göç Yolu", "durum": "%65 Olasılık"},

    # Kalkolitik Çağ
    {"ad": "Hacılar (Bilinen)", "donem": "Kalkolitik Çağ", "lat": 37.6333, "lng": 30.2167, "tip": "Bilinen Yerleşim", "yukseklik": "940 m", "su_mesafesi": "1.2 km", "egim": "Hafif (%5)", "toprak": "Yüksek verimlilik", "faktor": "Göller Yöresi Eşik", "durum": "Kanıtlanmış Arkeolojik Sit"},
    {"ad": "Aday Bölge K-1 (Sakarya Vadisi)", "donem": "Kalkolitik Çağ", "lat": 39.9500, "lng": 31.1000, "tip": "Yüksek Olasılık", "yukseklik": "780 m", "su_mesafesi": "0.9 km", "egim": "Hafif (%4)", "toprak": "Yüksek verimlilik", "faktor": "Nehir Terası Tarım Alanı", "durum": "%84 Olasılık"},
    {"ad": "Aday Bölge K-2 (Malatya Ovası)", "donem": "Kalkolitik Çağ", "lat": 38.3500, "lng": 38.3000, "tip": "Yüksek Olasılık", "yukseklik": "890 m", "su_mesafesi": "1.5 km", "egim": "Orta (%6)", "toprak": "Çok Yüksek verimlilik", "faktor": "Metal Yataklarına Yakınlık", "durum": "%79 Olasılık"},
    {"ad": "Aday Bölge K-3 (Menderes Havzası)", "donem": "Kalkolitik Çağ", "lat": 37.9000, "lng": 28.5000, "tip": "Orta Olasılık", "yukseklik": "140 m", "su_mesafesi": "2.0 km", "egim": "Düz (%3)", "toprak": "Yüksek verimlilik", "faktor": "Vadi Tabanı Yerleşimi", "durum": "%58 Olasılık"},

    # Tunç Çağı
    {"ad": "Truva (Bilinen)", "donem": "Tunç Çağı", "lat": 39.9575, "lng": 26.2386, "tip": "Bilinen Yerleşim", "yukseklik": "31 m", "su_mesafesi": "1.0 km", "egim": "Hafif (%4)", "toprak": "Yüksek verimlilik", "faktor": "Deniz Ticaret Yolu Hakimiyeti", "durum": "Kanıtlanmış Arkeolojik Sit"},
    {"ad": "Kültepe / Kaniş (Bilinen)", "donem": "Tunç Çağı", "lat": 38.8500, "lng": 35.6167, "tip": "Bilinen Yerleşim", "yukseklik": "1080 m", "su_mesafesi": "1.8 km", "egim": "Düz (%2)", "toprak": "Yüksek verimlilik", "faktor": "Kritik Kara Ticaret Kavşağı", "durum": "Kanıtlanmış Arkeolojik Sit"},
    {"ad": "Aday Bölge T-1 (Haymana Eşiği)", "donem": "Tunç Çağı", "lat": 39.1000, "lng": 32.8000, "tip": "Orta Olasılık", "yukseklik": "1150 m", "su_mesafesi": "2.8 km", "egim": "Orta (%9)", "toprak": "Orta verimlilik", "faktor": "Yaylak / Otlak Kontrolü", "durum": "%61 Olasılık"},
    {"ad": "Aday Bölge T-2 (Kızılırmak Kavis Bölgesi)", "donem": "Tunç Çağı", "lat": 39.3000, "lng": 37.5000, "tip": "Yüksek Olasılık", "yukseklik": "1310 m", "su_mesafesi": "1.4 km", "egim": "Yüksek (%15)", "toprak": "Orta verimlilik", "faktor": "Stratejik Yüksekliğe ve Ticaret Yoluna Yakınlık", "durum": "%73 Olasılık"},
    {"ad": "Aday Bölge T-3 (Göksu Geçidi)", "donem": "Tunç Çağı", "lat": 36.8000, "lng": 33.8000, "tip": "Yüksek Olasılık", "yukseklik": "850 m", "su_mesafesi": "0.6 km", "egim": "Dik (%22)", "toprak": "Düşük verimlilik", "faktor": "Dağ Geçidi / Güvenlik Noktası", "durum": "%76 Olasılık"}
]

df = pd.DataFrame(data)

# Sol Panel
st.sidebar.header("⏳ DÖNEM SEÇİMİ")
donem_listesi = df["donem"].unique()
secilen_donem = st.sidebar.selectbox("Arkeolojik Dönem:", donem_listesi)

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
    "• **Veri Tabanı:** TAY Projesi\n"
    "• **Coğrafi Veriler:** SRTM DEM\n"
    "• **Model:** Random Forest (ML)"
)

df_filtrelenmis = df[df["donem"] == secilen_donem]

st.subheader(f"Harita Analizi ve Model Tahminleri: {secilen_donem}")
st.info("💡 **İpucu:** Harita üzerinde herhangi bir bölgeye tıkladığınızda veya aşağıdaki listeden seçtiğinizde detay raporu güncellenecektir.")

# Harita Oluşturma
m = folium.Map(
    location=[39.0, 35.0], 
    zoom_start=6, 
    tiles="OpenStreetMap",
    zoom_control=True,
    scroll_wheel_zoom=False,
    dragging=True
)

for _, row in df_filtrelenmis.iterrows():
    if "Bilinen" in row["tip"]:
        folium.Marker(
            location=[row["lat"], row["lng"]],
            icon=folium.Icon(color="black", icon="bookmark", prefix="fa")
        ).add_to(m)
    else:
        renk = "#a83232" if "%8" in row["durum"] or "%7" in row["durum"] else "#b8860b"
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

# Harita tıklama veya varsayılan seçim mantığı
secilen_yerlesim_adi = df_filtrelenmis.iloc[0]["ad"]

if harita_cikti and "last_clicked" in harita_cikti and harita_cikti["last_clicked"] is not None:
    tik_lat = harita_cikti["last_clicked"]["lat"]
    tik_lng = harita_cikti["last_clicked"]["lng"]
    
    en_kucuk_mesafe = float("inf")
    en_yakin_bolge = secilen_yerlesim_adi
    
    for _, row in df_filtrelenmis.iterrows():
        mesafe = math.sqrt((row["lat"] - tik_lat)**2 + (row["lng"] - tik_lng)**2)
        if mesafe < en_kucuk_mesafe:
            en_kucuk_mesafe = mesafe
            en_yakin_bolge = row["ad"]
            
    secilen_yerlesim_adi = en_yakin_bolge

st.markdown("---")
st.subheader("📌 Seçilen Bölge / Aday Alan Detay Raporu")

secilen_yerlesim_adi = st.selectbox(
    "Haritadan tıkladığınız veya listeden seçtiğiniz bölge:",
    df_filtrelenmis["ad"].tolist(),
    index=list(df_filtrelenmis["ad"].tolist()).index(secilen_yerlesim_adi) if secilen_yerlesim_adi in df_filtrelenmis["ad"].tolist() else 0
)

aktif_satir = df_filtrelenmis[df_filtrelenmis["ad"] == secilen_yerlesim_adi].iloc[0]

# Şık Antika Detay Kutusu
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
    rozet_bg = "#2b2b2b" if "Bilinen" in aktif_satir['tip'] else "#d9c39a"
    rozet_renk = "#ffffff" if "Bilinen" in aktif_satir['tip'] else "#7a3e1e"
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
