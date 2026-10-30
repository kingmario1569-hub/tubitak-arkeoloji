"""Bütün betiklerin ortak ayarları ve yardımcı fonksiyonları.

Ayarları değiştirmek için SADECE bu dosyayı düzenleyin. Ön-kayıttan (ON_KAYIT.md)
sonra yapılan her değişiklik ON_KAYIT.md'deki "Sapmalar" tablosuna yazılmalıdır.
"""
from pathlib import Path

KOK = Path(__file__).resolve().parent
VERI = KOK / "veri"
HAM = VERI / "ham"
SONUC = KOK / "sonuclar"
GRAFIK = SONUC / "grafikler"

YERLESIM_CSV = VERI / "yerlesimler_temiz.csv"
DEGISKEN_CSV = SONUC / "degiskenler.csv"

# Çalışma bölgesi: (batı boylam, güney enlem, doğu boylam, kuzey enlem)
# Batı Anadolu + Göller Bölgesi. Bölge değişirse burayı ve ON_KAYIT.md'yi güncelleyin.
BOLGE_SINIRI = (26.0, 36.0, 32.5, 41.0)

RASTGELE = 42                      # Bütün rastgele işlemler için sabit tohum
DONEMLER = ["Neolitik", "Kalkolitik", "Tunc"]   # Hedef sınıflar (sıralı)

# ---- Başla / durdur kuralı (Protokol §2.3) ----
EN_AZ_YERLESIM = 50               # Dönem başına en az yerleşim
EN_FAZLA_DENGESIZLIK = 3.0        # En kalabalık / en az kalabalık dönem oranı

# ---- Değişkenler ve temaları (Karar belgesi §2.2) ----
# Tema adları grafiklerde ve "kayma" analizinde kullanılır.
TEMALAR = {
    "su_mesafe_m": "Su",
    "duz_arazi_orani_2km": "Tarım",
    "aluvyon": "Tarım",
    "aluvyon_orani_2km": "Tarım",
    "maden_mesafe_m": "Kaynak",
    "obsidiyen_mesafe_m": "Kaynak",
    "tpi_1km": "Savunma",
    "gorus_alani_km2": "Savunma",
    "egim_ort": "Savunma",
    "gecit_mesafe_m": "Hareket",
    "yukseklik_ort": "Genel",
    "yol_mesafe_m": "Önyargı",
    "koy_mesafe_m": "Önyargı",
}
ONYARGI_DEGISKENLERI = ["yol_mesafe_m", "koy_mesafe_m"]

# ---- Analiz ayarları (Protokol §6) ----
BLOK_BOYUTU_M = 20_000            # Mekânsal blok doğrulama için kare blok kenarı
KATMAN_SAYISI = 5                 # Çapraz doğrulama katman sayısı
AGAC_SAYISI = 500
PERMUTASYON_TEKRAR = 20           # Permütasyon önemi için tekrar
ETIKET_PERMUTASYON = 100          # H4 için etiket karıştırma testi tekrar sayısı

# ---- Hipotez eşikleri (ON_KAYIT.md ile AYNI olmalı) ----
ANLAMLILIK = 0.05
ETKI_ESIGI = 0.04                 # Kruskal-Wallis epsilon-kare
H4_DOGRULUK_ESIGI = 0.45          # Mekânsal doğrulamada dengeli doğruluk

# Her alt hipotez: hangi değişken, hangi iki dönem, beklenen yön.
# "kucuk": ilk dönemin değeri ikinciden küçük olmalı; "buyuk": büyük olmalı.
HIPOTEZLER = {
    "H1 Tarım": [
        ("su_mesafe_m", "Neolitik", "Tunc", "kucuk"),
        ("duz_arazi_orani_2km", "Neolitik", "Tunc", "buyuk"),
    ],
    "H2 Kaynak": [
        ("maden_mesafe_m", "Kalkolitik", "Neolitik", "kucuk"),
        ("maden_mesafe_m", "Tunc", "Neolitik", "kucuk"),
    ],
    "H3 Savunma": [
        ("tpi_1km", "Tunc", "Neolitik", "buyuk"),
        ("gorus_alani_km2", "Tunc", "Neolitik", "buyuk"),
    ],
}


def utm_epsg(boylam_ortalama: float) -> int:
    """Bölgenin ortalama boylamına göre UTM (WGS84, kuzey) EPSG kodu."""
    zon = int((boylam_ortalama + 180) // 6) + 1
    return 32600 + zon


def klasorleri_hazirla():
    for k in (VERI, HAM, SONUC, GRAFIK):
        k.mkdir(parents=True, exist_ok=True)
