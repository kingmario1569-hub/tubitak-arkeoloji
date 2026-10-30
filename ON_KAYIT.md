# Ön-Kayıt (Pre-registration)

> **Öğrenci için:** Bu dosyayı kendi cümlelerinle doldur ve **veri analizine başlamadan önce** GitHub deponun ana klasörüne `ON_KAYIT.md` adıyla commit'le. Commit mesajı: `Ön-kayıt: hipotezler ve analiz planı sabitlendi`. Bundan sonra bu metni değiştirme; değişiklik gerekirse en alttaki "Sapmalar" bölümüne tarihiyle ve gerekçesiyle ekle.

**Proje:** [PROJE BAŞLIĞI]
**Öğrenci:** [AD SOYAD] · **Danışman öğretmen:** [AD SOYAD]
**Ön-kayıt tarihi:** [GG.AA.YYYY] (commit tarihi esas alınır)

---

## 1. Araştırma sorusu
[Ana soruyu tek cümleyle yaz.]

## 2. Veri
- **Bölge sınırı:** [enlem/boylam aralığı veya il listesi]
- **Kaynaklar:** [DEFC / LuwianSiteAtlas / XRONOS; indirme tarihleri]
- **Dönem başına yerleşim sayısı (temizleme sonrası):** Neolitik [n], Kalkolitik [n], Tunç [n]
- **Hedef değişken:** İlk iskân dönemi
- **Çıkarılacaklar:** Koordinat kesinliği 3 olanlar, dönemi belirsiz olanlar, bölge dışındakiler

## 3. Hipotezler

| # | Hipotez (yönüyle birlikte) | Değişken(ler) | Test | "Destekleniyor" eşiği |
|---|---|---|---|---|
| H1 | [ ] | [ ] | Kruskal-Wallis + ε² | p < 0,05 ve ε² ≥ [ ] ve beklenen yön |
| H2 | [ ] | [ ] | Kruskal-Wallis + ε² | [ ] |
| H3 | [ ] | [ ] | Kruskal-Wallis + ε² | [ ] |
| H4 | [ ] | Tüm değişkenler | Random Forest, mekânsal blok doğrulama | Dengeli doğruluk ≥ [ ] |
| H0 | Modern yol mesafesi en önemli 2 değişkenden biridir | `yol_mesafe_m` | Permütasyon önemi | İlk 2'de |

**Her hipotezin literatürdeki dayanağı:** [Her hipotez için 1–2 kaynak]

## 4. Analiz planı
- Değişken listesi ve tanımları: `veri sözlüğü` ([bağlantı])
- Model: Random Forest (500 ağaç, `class_weight="balanced"`, `random_state=42`); karşılaştırma: lojistik regresyon
- Doğrulama: [BLOK BOYUTU] km mekânsal bloklar, 5 katmanlı `GroupKFold`; karşılaştırma için rastgele `KFold`
- Duyarlılık analizleri: tek dönemli yerleşimler · tek kaynak · sadece kesin koordinatlar
- Gizli test alt bölgesi: [hangi alan; en başta ayrıldı, en sonda bir kez kullanılacak]

## 5. Sonuç ne olursa ne diyeceğim?
- H1 desteklenmezse: [ ]
- H0 desteklenirse (yol mesafesi en önemli çıkarsa): [ ]
- H4 desteklenmezse (model şans düzeyinde kalırsa): [ ]

---

## Sapmalar
*(Ön-kayıttan sonra yapılan her değişiklik: tarih, ne değişti, neden.)*

| Tarih | Değişiklik | Gerekçe |
|---|---|---|
| | | |
