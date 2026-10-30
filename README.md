# Anadolu'da Üç Çağın Yerleşim Seçimi

Neolitik, Kalkolitik ve Tunç Çağı yerleşimlerinin coğrafi konum özelliklerini karşılaştıran,
araştırma önyargısı kontrollü bir makine öğrenmesi çalışması (TÜBİTAK 2204-A).

**Temel ilke:** Bu depodaki hiçbir sayı elle yazılmaz. Yerleşim listesi yayımlanmış kaynaklardan derlenir.
Değişkenler gerçek coğrafi verilerden hesaplanır. Sonuçları betikler üretir. Uygulama (`app.py`) yalnızca bu sonuçları gösterir.

## Akış

```
veri/yerlesimler_temiz.csv ──► 00_veri_kontrol.py ──► (hata yoksa) ──► 01_degisken_hesapla.py
                                                                            │
                                                         sonuclar/degiskenler.csv
                                                                            │
                                    ON_KAYIT.md commit'lenir ──► 02_model.py
                                                                            │
                                                  sonuclar/*.csv, *.json, grafikler/*.png
                                                                            │
                                                                        app.py
```

| Dosya | Görevi |
|---|---|
| `calistir.ipynb` | **Google Colab defteri:** Bütün adımları sırayla, kurulum gerektirmeden çalıştırır (önerilen yol) |
| `ortak.py` | Bütün ayarlar: çalışma bölgesi (`BOLGE_SINIRI`), dönemler, değişkenler, eşikler, hipotezler. **Ön-kayıttan sonra değiştirilmez.** |
| `veri_hazirla_luwian.py` | LuwianSiteAtlas dosyalarını (veri/kaynak/luwian/) proje tablosuna ve maden dosyasına dönüştürür |
| `00_veri_kontrol.py` | Yerleşim tablosunu denetler (boş hücre, koordinat hatası, yakın kayıt, dönem sayıları) ve başla/durdur kararını verir |
| `01_degisken_hesapla.py` | Copernicus DEM'den yükseklik, eğim, düz arazi oranı, TPI, görüş alanı; vektör katmanlardan su, maden, obsidiyen, geçit, yol ve köy mesafelerini hesaplar |
| `02_model.py` | Kruskal-Wallis + ε², Random Forest (mekânsal ve rastgele doğrulama), lojistik regresyon, etiket karıştırma testi, permütasyon önemi, kısmi bağımlılık, dönem geçişi analizi, duyarlılık analizleri, hipotez kararları |
| `app.py` | Streamlit uygulaması; sadece `sonuclar/` klasörünü okur |

## Kurulum

**Google Colab (önerilen):** Depoyu Colab'da açın ve şu hücreyi çalıştırın:
```
!git clone https://github.com/[KULLANICI]/tubitak-arkeoloji.git
%cd tubitak-arkeoloji
!pip install -r requirements-analiz.txt
```

**Kendi bilgisayarınızda:** Python 3.11+ ile `pip install -r requirements-analiz.txt`

## Adım adım

### 1. Yerleşim tablosunu hazırlayın
`veri/yerlesimler_temiz.csv` dosyasını kaynaklardan (DEFC, LuwianSiteAtlas, XRONOS, TAY) derleyin. Sütunlar:

| Sütun | Açıklama |
|---|---|
| `site_id` | Benzersiz kimlik (ör. `DEFC_0123`) |
| `ad` | Yerleşim adı |
| `lat`, `lon` | Ondalık derece (WGS84) |
| `koord_kesinlik` | 1 kesin · 2 köy/ilçe düzeyi · 3 tahmini (3'ler analize girmez) |
| `donemler` | Kaynakta geçen bütün dönemler, `;` ile ayrılmış |
| `ilk_donem` | `Neolitik`, `Kalkolitik` veya `Tunc` (hedef değişken) |
| `tek_donemli` | `evet` / `hayir` |
| `kaynak` | Kaynak adı |
| `kaynak_kayit` | Kaynaktaki kayıt bağlantısı veya numarası |
| `hoyuk_yaricap_m` | *(isteğe bağlı)* Büyük höyükler için höyük yarıçapı (varsayılan 250 m) |

Sonra: `python 00_veri_kontrol.py`. Hata varsa düzeltin; karar "DURDUR" ise bölgeyi genişletin.

### 2. Coğrafi katmanları indirin
`veri/ham/` altına (ayrıntı ve bağlantılar `veri/KAYNAKLAR.md`'de). **DEM indirmek gerekmez**; betik Copernicus DEM'i internetten gerektiği kadar okur. Bir katman eksikse o değişken hesaplanmaz, hiçbir değer uydurulmaz.

### 3. Değişkenleri hesaplayın
`python 01_degisken_hesapla.py` → `sonuclar/degiskenler.csv`.
**Elle kontrol:** 3 yerleşimin yükseklik ve su mesafesini QGIS'te ölçün, tabloyla karşılaştırın ve sonucu `veri/TEMIZLEME_GUNLUGU.md`'ye yazın.

### 4. Ön-kaydı commit'leyin
`ON_KAYIT.md`'yi doldurun, `ortak.py`'deki eşik ve hipotezlerin aynı olduğunu kontrol edin, commit'leyin:
`git commit -m "Ön-kayıt: hipotezler ve analiz planı sabitlendi"`

### 5. Analizi çalıştırın
`python 02_model.py` (birkaç dakika–yarım saat; yerleşim sayısına bağlı). Bütün çıktılar `sonuclar/` altında.

### 6. Uygulamayı yayınlayın
`sonuclar/` klasörünü de commit'leyin (küçük dosyalardır). Streamlit Cloud'da ana dosya `app.py`, gereksinim dosyası `requirements.txt`.
Yerel deneme: `pip install -r requirements.txt && streamlit run app.py`

## Yöntem notları (rapora girecek)
- **Höyük düzeltmesi:** Höyükler zamanla yükselir; Tunç Çağı höyükleri genellikle daha yüksektir. Bu, savunma değişkenlerini yapay olarak şişirir. Bu yüzden yükseklik, eğim, TPI ve görüş alanı höyüğün dışındaki doğal zeminden ölçülür ve höyüğün kendisi görüş alanında engel sayılmaz.
- **Görüş alanı:** 360 ışınlı basit görüş hattı hesabı, 5 km yarıçap, 2 m gözlemci, Dünya eğriliği ve kırılma düzeltmesi. Raporda "yaklaşık görüş alanı" olarak anılmalı; birkaç yerleşimde QGIS Viewshed ile karşılaştırılması önerilir.
- **Mekânsal doğrulama:** 20 × 20 km bloklar, `StratifiedGroupKFold`. Rastgele doğrulama sadece karşılaştırma için raporlanır.
- **Önem ölçüsü:** Test katmanlarında permütasyon önemi (dengeli doğruluktaki düşüş).
- **H4 anlamlılığı:** Dönem etiketleri 100 kez karıştırılıp model yeniden değerlendirilir (`permutation_test_score`).

## Kaynaklar
Veri kaynaklarının tam listesi ve lisansları: `veri/KAYNAKLAR.md`. Yöntem kaynakları: proje raporu.
