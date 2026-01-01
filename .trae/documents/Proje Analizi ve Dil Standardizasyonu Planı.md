# Proje Analizi, İyileştirme ve Dil Standardizasyonu Planı

Mevcut analizlerime göre proje genel hatlarıyla yapılandırılmış olsa da (Python/FastAPI, Solidity, Airflow), `bugbounty_7_agents_template` klasörü altında düzeltilmesi gereken Türkçe isimlendirmeler (`envanter.py` vb.) ve yorum satırları bulunmaktadır. Aşağıdaki plan, projenin "Tamam" statüsüne ulaşması için gereken adımları içerir.

## 1. Dil Uyumluluğu ve Kod İçeriği Kontrolü (Öncelikli)
Kritik "Tamamen İngilizce Proje" kuralını sağlamak için:
- **Dosya Yeniden Adlandırma:** `bugbounty_7_agents_template/agents/envanter.py` dosyasını `inventory.py` olarak değiştirme.
- **Kod İçeriği Çevirisi:** `agents/` altındaki dosyalarda tespit edilen Türkçe loglar ("nuclei bulguları"), yorumlar ve help stringlerini İngilizceye çevirme.
- **Otomatik Tarama:** Tüm proje genelinde regex ile Türkçe karakter veya kelime taraması yapıp temizleme.

## 2. Bileşen ve Entegrasyon Testleri
Sistemin çalışırlığını doğrulamak için:
- **Backend Testleri:** `tests/` dizinindeki Pytest testlerini çalıştırma ve hataları raporlama.
- **Smart Contract Testleri:** `smart_contract/` dizininde Hardhat testlerini (`npx hardhat test`) çalıştırma.
- **Bağımlılık Kontrolü:** `requirements.txt` ve `package.json` dosyalarının güncelliğini ve uyumluluğunu doğrulama.

## 3. Hata Tespiti ve Statik Analiz
- **Linting:** Python kodları için statik analiz yaparak olası syntax hatalarını veya kullanılmayan değişkenleri tespit etme.
- **Log İncelemesi:** Testler sırasında oluşan hata loglarını analiz edip kök nedenleri belirleme.

## 4. Dokümantasyon ve Performans Değerlendirmesi
- **Doküman Güncellemesi:** Yapılan isim değişikliklerinin (örn. `envanter.py`) `README.md` ve diğer dokümanlara yansıdığını doğrulama.
- **Mimari İnceleme:** Docker yapılandırması ve veritabanı şemalarını (Alembic) performans ve ölçeklenebilirlik açısından gözden geçirme.

## 5. Sonuç Raporlama
- 10.01 tarihine kadar tamamlanacak şekilde, yapılan tüm testlerin sonuçlarını, düzeltilen hataları ve sistemin nihai durumunu ("Tamam" veya "Tamam Değil") içeren detaylı Türkçe raporun hazırlanması.
