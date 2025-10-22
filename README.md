# Mastermind Web Oyunu

Bu depo, eşsiz renk kombinasyonlarına sahip Mastermind oyununu Türkçe bir web arayüzüyle sunar. Flask tabanlı arka uç oyun mantığını yürütürken, statik HTML/CSS/JS dosyaları kullanıcıların renk seçmelerini, mod belirlemelerini ve tahmin geçmişini takip etmelerini sağlar.

## Özellikler
- Aynı oyunda "Oyuncu vs Oyuncu" ve "Oyuncu vs Yapay Zekâ" modları.
- Sırayla tahmin ("Birer Birer") seçeneğiyle oyuncuların dönüşümlü oynaması.
- Yinelenen renklere izin vermeyen gizli kod ve tahmin doğrulaması.
- Türkçe kullanıcı arayüzü, renk paleti butonları ve tur özeti.

## Gereksinimler
- Python 3.9 veya daha yeni bir sürüm
- `pip` paket yöneticisi
- (Önerilir) Sanal ortam aracı (`venv`, `virtualenv` vb.)

## Kurulum
1. Depoyu yerel makinenize kopyalayın:
   ```bash
   git clone <repo-url>
   cd mastermind-game
   ```
2. (İsteğe bağlı) Sanal ortam oluşturun ve etkinleştirin:
   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```
3. Gerekli Python paketlerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Uygulamayı Çalıştırma
1. Flask uygulamasını başlatın:
   ```bash
   python app.py
   ```
2. Tarayıcınızda `http://127.0.0.1:5000/` adresini açın.
3. Sol taraftaki menüden oyun modunu, kod uzunluğunu ve maksimum deneme sayısını seçin; renk butonlarını kullanarak tahminlerinizi yapın.

## Geliştirme İpuçları
- Kod değişikliklerinden sonra tarayıcıyı yenileyerek yeni arayüzü görebilirsiniz.
- Sunucu koduna yaptığınız değişiklikler için Flask'ı geliştirme modunda çalıştırmak isterseniz şu komutları kullanabilirsiniz:
  ```bash
  export FLASK_APP=app.py
  export FLASK_ENV=development  # Windows PowerShell: $env:FLASK_ENV = "development"
  flask run
  ```
- Test amaçlı olarak "Oyunu Sıfırla" düğmesini kullanarak oturumdaki mevcut oyunu temizleyebilirsiniz.

## Lisans
Bu proje aksi belirtilmedikçe ticari olmayan kişisel kullanım içindir. Lisans bilgisini özelleştirmek için bu bölümü güncelleyebilirsiniz.
