# BMG-Proje-Puanlama
BTU Bilgisayar Mühendisliğine Giriş dersi proje ödevi puanlayıcı. Öğrencilerin yaptıkları websitelerini inceleyeyip puanlayan ve bunu bir csv dosyasına kaydeden python scripti.

## Özellikler

- Belirtilen URL üzerinden sayfa sayısı ve içerik özelliklerini analiz eder.

- Her sayfa için
  - Başlık varlığı
  - Tablo varlığı
  - Uzun paragraflar
  - Resimler
  - Yorum satırları
- Skor parametrelerinin konfigürasyonu **config.json**.
- Genel skor hesaplaması (100 üzerinden).
- Sonuçları CSV formatında dışa aktarma.

## Başlarken

```bash
git clone https://github.com/Fatihparm/BMG-Proje-Puanlama-.git

pip install -r requirements.txt
```

- Scriptin çalışması için aynı dizinde içinde urllerin ve öğrenci adlarının bulunduğu bir txt dosyası olması gerekir. Örneğin: `urls.txt`

Bu işlemleri tamamladıktan sonra çalıştırmaya hazırız. Kodu çalıştırmak için derleyiciden notlandir.py'yi run edebilir veya;

```bash
python notlandir.py urls.txt log.txt
```
komutunu çalıştırabilirsiniz.

### Sonuçlar

- Her sayfa için detaylı analiz sonuçları log.txt dosyasına yazılır.
- Nihai skorlar sonuclar.csv dosyasına kaydedilir.

## Config.json yapısı

- **weights:** Sayfa öğelerinin önem derecelerini belirler.

    - **index:** Sayfa başlıklarının her biri için verilen puan (örneğin, 4 puan).
    - **max_index_score:** Başlıkların toplamda alabileceği maksimum puan.
    - **header:** Başlık öğesi için belirlenen ağırlık (örneğin, 20 puan).
    - **paragraph:** Uzun paragraf öğesi için belirlenen ağırlık.
    - **image:** Resim varlığı için belirlenen ağırlık.
    - **comments:** Yorum satırları varlığı için belirlenen ağırlık.
    - **table:** Tablo varlığı için belirlenen ağırlık.
- **tresholds:** Her öğenin değerlendirilmesi için gerekli minimum şartları belirler.

    - **header_min_pages:** En az kaç sayfada başlık bulunması gerektiği (örneğin, 1 sayfa).
    - **paragraph_length:** Paragrafların en az kaç karakter uzunluğunda olması gerektiği (örneğin, 300 karakter).
    - **image_count:** En az kaç resim bulunması gerektiği (örneğin, 1 resim).

Bu ayarlar, sayfa içeriklerini analiz ederken her öğe için gerekli puanları ve minimum gereksinimleri belirler. Bunları değiştirip farklı puanlama sistemleri tasarlayabilirsiniz. Tabii toplam skorun **100**'ü geçmediğinden emin olmalısınız.

# Teşekkürler...
