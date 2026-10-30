"""ADIM 1: Her yerleşim için coğrafi değişkenleri GERÇEK verilerden hesaplar.

Girdi :
  veri/yerlesimler_temiz.csv                 (00_veri_kontrol.py'den hatasız geçmiş olmalı)
  Copernicus GLO-30 DEM                      (internetten otomatik okunur, indirme gerekmez)
  veri/ham/ altındaki katmanlar (aşağıdaki KATMANLAR sözlüğüne bakın; her biri isteğe bağlıdır)
Çıktı :
  sonuclar/degiskenler.csv                   (her yerleşim için bir satır)
  sonuclar/degisken_hesaplama.json           (hangi katman kullanıldı, hangisi atlandı)

ÖNEMLİ: Bir katmanın dosyası yoksa o değişken HESAPLANMAZ ve tabloya hiç eklenmez.
Hiçbir değer tahminle, örnekle veya elle doldurulmaz.

Çalıştırma:  python 01_degisken_hesapla.py
"""
import json
import math
import os
import time

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from shapely.geometry import box

import ortak as o

# GDAL'ın uzak (bulut) dosyaları verimli okuması için
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")

# ---------------------------------------------------------------------------
# AYARLAR
# ---------------------------------------------------------------------------
# DEM: Copernicus GLO-30 (30 m), AWS açık veri deposu. Yerel kopya kullanmak için
# DEM_YEREL_KLASOR'e .tif dosyalarını koyun; klasör doluysa internet kullanılmaz.
DEM_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/"
           "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
           "Copernicus_DSM_COG_10_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif")
DEM_YEREL_KLASOR = o.HAM / "dem"

PENCERE_M = 6_000            # Her yerleşim için okunacak DEM penceresinin yarıçapı
GORUS_YARICAP_M = 5_000      # Görüş alanı yarıçapı
GOZLEMCI_M = 2.0             # Gözlemci boyu
ISIN_SAYISI = 360            # Görüş alanı için ışın sayısı (her derecede bir)

# Höyüğün kendi yüksekliği sonuçları bozmasın diye merkezdeki höyük alanı hariç tutulur.
# (Uzun süre iskân edilen höyükler yüksektir; Tunç Çağı höyükleri genellikle daha
#  yüksektir. Höyük hariç tutulmazsa "savunma" değişkenleri yapay olarak şişer.)
# Doğal zemin, höyüğün hemen dışındaki 250 m'lik halkadan ölçülür.
# Büyük höyüklerde (ör. Çatalhöyük ~450 x 275 m) bu değer yetmeyebilir: CSV'ye
# isteğe bağlı "hoyuk_yaricap_m" sütunu eklenirse, o yerleşim için o değer kullanılır.
HOYUK_YARICAP_M = 250
ZEMIN_HALKA_M = 250

# Vektör katmanlar (hepsi isteğe bağlı). Dosya yoksa ilgili değişken atlanır.
KATMANLAR = {
    # HydroRIVERS (hydrosheds.org) – Türkiye'yi kapsayan bölge dosyası
    "akarsu": {"dosya": o.HAM / "hydrorivers" / "HydroRIVERS_v10_eu.shp",
               "filtre_sutun": "ORD_STRA", "en_az": 4},        # Strahler derecesi >= 4 (büyük, kalıcı akarsular)
    # HydroLAKES – göller
    "gol": {"dosya": o.HAM / "hydrolakes" / "HydroLAKES_polys_v10.shp",
            "filtre_sutun": "Lake_area", "en_az": 1.0},         # >= 1 km² göller
    # MTA jeoloji haritasından sadece Kuvaterner alüvyon poligonları (QGIS'te ayıklayıp kaydedin)
    "aluvyon": {"dosya": o.HAM / "aluvyon.gpkg"},
    # Maden kaynakları: lat, lon, tur, kaynak sütunlu CSV
    "maden": {"dosya": o.HAM / "madenler.csv"},
    # Obsidiyen kaynakları: lat, lon, ad, kaynak sütunlu CSV
    "obsidiyen": {"dosya": o.HAM / "obsidiyen.csv"},
    # Doğal geçiş koridorları: QGIS'te en düşük maliyetli yol analiziyle üretilen çizgiler
    "gecit": {"dosya": o.HAM / "gecit_koridorlari.gpkg"},
    # OpenStreetMap (Geofabrik Türkiye shapefile'ı) – ÖNYARGI değişkenleri
    "yol": {"dosya": o.HAM / "osm" / "gis_osm_roads_free_1.shp",
            "filtre_sutun": "fclass",
            "degerler": ["motorway", "trunk", "primary", "secondary", "tertiary",
                         "unclassified", "residential"]},
    "koy": {"dosya": o.HAM / "osm" / "gis_osm_places_free_1.shp",
            "filtre_sutun": "fclass", "degerler": ["city", "town", "village"]},
}


# ---------------------------------------------------------------------------
# DEM YARDIMCILARI
# ---------------------------------------------------------------------------
def dem_kaynaklari(bati, guney, dogu, kuzey):
    """Pencereyi kapsayan DEM döşemelerini açar (yerel klasör varsa oradan)."""
    yerel = sorted(DEM_YEREL_KLASOR.glob("*.tif")) if DEM_YEREL_KLASOR.exists() else []
    if yerel:
        acik = [rasterio.open(p) for p in yerel]
        return [a for a in acik if not (a.bounds.right < bati or a.bounds.left > dogu or
                                        a.bounds.top < guney or a.bounds.bottom > kuzey)]
    acik = []
    for enlem in range(math.floor(guney), math.floor(kuzey) + 1):
        for boylam in range(math.floor(bati), math.floor(dogu) + 1):
            url = DEM_URL.format(ns="N" if enlem >= 0 else "S", lat=abs(enlem),
                                 ew="E" if boylam >= 0 else "W", lon=abs(boylam))
            try:
                acik.append(rasterio.open("/vsicurl/" + url))
            except rasterio.errors.RasterioIOError:
                pass  # Denizdeki döşemeler yoktur
    return acik


def dem_penceresi(lat, lon):
    """Yerleşim çevresindeki DEM'i ve her pikselin merkeze uzaklığını (m) döndürür."""
    d_lat = PENCERE_M / 111_320
    d_lon = PENCERE_M / (111_320 * math.cos(math.radians(lat)))
    sinir = (lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat)
    kaynaklar = dem_kaynaklari(*sinir)
    if not kaynaklar:
        raise RuntimeError("DEM döşemesi bulunamadı")
    try:
        z, donusum = merge(kaynaklar, bounds=sinir)
    finally:
        for k in kaynaklar:
            k.close()
    z = z[0].astype("float64")
    # Piksel boyutları (metre). Copernicus coğrafi koordinatlıdır (derece).
    dy = abs(donusum.e) * 111_320
    dx = abs(donusum.a) * 111_320 * math.cos(math.radians(lat))
    # Merkezin piksel konumu
    sut0, sat0 = ~donusum * (lon, lat)
    satirlar, sutunlar = np.indices(z.shape)
    mesafe = np.hypot((satirlar + 0.5 - sat0) * dy, (sutunlar + 0.5 - sut0) * dx)
    return z, mesafe, dx, dy, (sat0, sut0)


def egim_derece(z, dx, dy):
    gy, gx = np.gradient(z, dy, dx)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def gorus_alani_km2(z, dx, dy, merkez, z0, hoyuk_m):
    """Basit ışın izleme ile görüş alanı (km²).

    Merkezden 360 yöne ışın gönderilir. Bir nokta, gözlemciden bakış açısı o ışın
    üzerindeki önceki bütün noktaların açısından büyük veya eşitse görünür sayılır.
    Dünya eğriliği ve kırılma düzeltmesi uygulanır. QGIS Viewshed'e yakın sonuç verir;
    raporda "yaklaşık görüş alanı" olarak anılmalıdır.

    Gözlemci, höyüğün çevresindeki doğal zeminin 2 m üstündedir. Höyüğün kendisi
    (merkezden hoyuk_m içi) engel sayılmaz; aksi hâlde yerleşimin sonradan
    biriken toprağı, kurulduğu andaki görüşü kapatmış gibi hesaplanırdı.
    """
    sat0, sut0 = merkez
    adim = min(dx, dy)
    mesafeler = np.arange(hoyuk_m, GORUS_YARICAP_M + adim, adim)
    acilar = np.linspace(0, 2 * np.pi, ISIN_SAYISI, endpoint=False)
    sat = sat0 - np.outer(np.cos(acilar), mesafeler) / dy
    sut = sut0 + np.outer(np.sin(acilar), mesafeler) / dx
    gecerli = (sat >= 0) & (sat < z.shape[0]) & (sut >= 0) & (sut < z.shape[1])
    zi = np.full(sat.shape, np.nan)
    zi[gecerli] = z[sat[gecerli].astype(int), sut[gecerli].astype(int)]
    egrilik = mesafeler ** 2 / (2 * 6_371_000) * (1 - 0.13)
    egim = (zi - egrilik - z0) / mesafeler
    egim = np.where(np.isnan(egim), -np.inf, egim)
    onceki_max = np.maximum.accumulate(egim, axis=1)
    onceki_max = np.concatenate([np.full((ISIN_SAYISI, 1), -np.inf), onceki_max[:, :-1]], axis=1)
    gorunur = (egim >= onceki_max) & np.isfinite(egim)
    hucre_alani = mesafeler * (2 * np.pi / ISIN_SAYISI) * adim       # m²
    return float((gorunur * hucre_alani).sum() / 1e6)


def dem_degiskenleri(lat, lon, hoyuk_m=HOYUK_YARICAP_M):
    z, d, dx, dy, merkez = dem_penceresi(lat, lon)
    egim = egim_derece(z, dx, dy)
    zemin_halka = (d > hoyuk_m) & (d <= hoyuk_m + ZEMIN_HALKA_M)
    z_zemin = float(np.median(z[zemin_halka]))
    cevre = (d > hoyuk_m) & (d <= 1000)
    return {
        # Höyük dışındaki doğal zeminin ortalama yüksekliği
        "yukseklik_ort": float(z[zemin_halka].mean()),
        # Yerleşimin hemen çevresindeki ortalama eğim (yaklaşım zorluğu)
        "egim_ort": float(egim[zemin_halka].mean()),
        # 2 km içinde eğimi 5 dereceden az olan alanın yüzdesi (tarıma uygun düzlük)
        "duz_arazi_orani_2km": float((egim[d <= 2000] < 5).mean() * 100),
        # Topografik konum: doğal zemin, 1 km çevresinin ortalamasından ne kadar yüksek?
        "tpi_1km": float(z_zemin - z[cevre].mean()),
        "gorus_alani_km2": gorus_alani_km2(z, dx, dy, merkez, z_zemin + GOZLEMCI_M, hoyuk_m),
    }


# ---------------------------------------------------------------------------
# VEKTÖR YARDIMCILARI
# ---------------------------------------------------------------------------
def katman_oku(ad, sinir_wgs84, epsg):
    ayar = KATMANLAR[ad]
    yol = ayar["dosya"]
    if not yol.exists():
        return None, f"ATLANDI: {yol} bulunamadı"
    if yol.suffix.lower() == ".csv":
        t = pd.read_csv(yol)
        g = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t["lon"], t["lat"]), crs=4326)
    else:
        g = gpd.read_file(yol, bbox=sinir_wgs84)
    if "filtre_sutun" in ayar:
        if "degerler" in ayar:
            g = g[g[ayar["filtre_sutun"]].isin(ayar["degerler"])]
        else:
            g = g[g[ayar["filtre_sutun"]] >= ayar["en_az"]]
    if g.empty:
        return None, f"ATLANDI: {yol.name} bölgede hiç öğe içermiyor"
    return g.to_crs(epsg), f"kullanıldı: {yol.name} ({len(g)} öğe)"


def en_yakin_mesafe(noktalar, katman):
    """Her nokta için katmandaki en yakın öğeye mesafe (m)."""
    j = gpd.sjoin_nearest(noktalar[["geometry"]], katman[["geometry"]], distance_col="m", how="left")
    return j.groupby(level=0)["m"].min().reindex(noktalar.index)


# ---------------------------------------------------------------------------
def main():
    o.klasorleri_hazirla()
    df = pd.read_csv(o.YERLESIM_CSV)
    df = df[df["koord_kesinlik"] != 3].reset_index(drop=True)
    epsg = o.utm_epsg(df["lon"].mean())
    noktalar = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(epsg)
    pay = 0.5  # derece; katmanları bölgenin biraz dışından da oku
    sinir = box(df.lon.min() - pay, df.lat.min() - pay, df.lon.max() + pay, df.lat.max() + pay)
    sinir = tuple(sinir.bounds)
    gunluk = {"utm_epsg": epsg, "yerlesim_sayisi": len(df), "katmanlar": {}}

    # --- DEM değişkenleri ---
    print(f"DEM değişkenleri hesaplanıyor ({len(df)} yerleşim)...")
    satirlar, hatalar = [], []
    t0 = time.time()
    for i, r in df.iterrows():
        try:
            hoyuk = r["hoyuk_yaricap_m"] if "hoyuk_yaricap_m" in df and pd.notna(r.get("hoyuk_yaricap_m")) else HOYUK_YARICAP_M
            satirlar.append(dem_degiskenleri(r.lat, r.lon, float(hoyuk)))
        except Exception as e:  # Hata olursa değer UYDURULMAZ, boş bırakılır ve kaydedilir
            satirlar.append({})
            hatalar.append({"site_id": r.site_id, "hata": str(e)})
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(df)}  ({time.time() - t0:.0f} sn)")
    sonuc = pd.concat([df.drop(columns="geometry", errors="ignore"), pd.DataFrame(satirlar)], axis=1)
    gunluk["katmanlar"]["dem"] = f"kullanıldı: Copernicus GLO-30 ({len(hatalar)} yerleşimde hata)"
    gunluk["dem_hatalari"] = hatalar

    # --- Vektör değişkenleri ---
    for ad, sutun in [("akarsu", "su_mesafe_m"), ("maden", "maden_mesafe_m"),
                      ("obsidiyen", "obsidiyen_mesafe_m"), ("gecit", "gecit_mesafe_m"),
                      ("yol", "yol_mesafe_m"), ("koy", "koy_mesafe_m")]:
        katman, durum = katman_oku(ad, sinir, epsg)
        gunluk["katmanlar"][ad] = durum
        print(f"  {ad}: {durum}")
        if katman is not None:
            sonuc[sutun] = en_yakin_mesafe(noktalar, katman).to_numpy()

    # Göller varsa su mesafesi = min(akarsu, göl)
    gol, durum = katman_oku("gol", sinir, epsg)
    gunluk["katmanlar"]["gol"] = durum
    print(f"  gol: {durum}")
    if gol is not None:
        gol_m = en_yakin_mesafe(noktalar, gol).to_numpy()
        sonuc["su_mesafe_m"] = np.fmin(sonuc["su_mesafe_m"], gol_m) if "su_mesafe_m" in sonuc else gol_m

    aluvyon, durum = katman_oku("aluvyon", sinir, epsg)
    gunluk["katmanlar"]["aluvyon"] = durum
    print(f"  aluvyon: {durum}")
    if aluvyon is not None:
        birlesik = aluvyon.union_all()
        sonuc["aluvyon"] = noktalar.within(birlesik).astype(int).to_numpy()
        tampon = noktalar.buffer(2000)
        sonuc["aluvyon_orani_2km"] = (tampon.intersection(birlesik).area / tampon.area * 100).to_numpy()

    sonuc.to_csv(o.DEGISKEN_CSV, index=False)
    (o.SONUC / "degisken_hesaplama.json").write_text(
        json.dumps(gunluk, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nKaydedildi: {o.DEGISKEN_CSV}")
    print("Şimdi 3 yerleşimin değerlerini QGIS'te elle kontrol edin (Protokol §5, madde 6).")


if __name__ == "__main__":
    main()
