# Araba Tamir ve Modernizasyon Planı (Bounty Platform Repair Plan)

Analizlerime göre, "arabanın" motoru (Backend) çalışıyor ancak trafiğe çıkması için gereken kaporta (Frontend) ve kontak anahtarı (Kullanıcı Sistemi) eksik. İşte aracınızı trafiğe (pazara) çıkarmak için hazırladığım onarım planı:

## 1. Teşhis (Diagnosis)
*   **Motor (Backend):** `FastAPI` motoru sağlam, ancak ateşleme sistemi (Auth/Login) manuel anahtar (API Key) ile çalışıyor. Modern bir kontak (JWT Login) lazım.
*   **Şasi (Database):** `Jobs` tablosu var, ancak aracı kimin sürdüğünü kaydedecek `Users` tablosu yok.
*   **Kaporta (Frontend):** Hiç yok. Kullanıcılar motorun üzerine oturup kabloları (API) elle bağlıyor. Acil bir kokpit (Dashboard) lazım.

## 2. Onarım Planı (Repair Plan)

### Adım 1: Ateşleme Sistemi ve Şasi Güçlendirmesi (Backend Update)
*   **Süre:** ~30 Dakika
*   **İşlem:**
    1.  `backend/models.py` dosyasına `User` tablosu eklenecek.
    2.  `backend/main.py` dosyasına `/auth/register` ve `/auth/login` (JWT) özellikleri eklenecek.
    3.  `create_job` fonksiyonu, işi başlatan kullanıcıyı kaydedecek şekilde güncellenecek.

### Adım 2: Kaporta ve Kokpit Montajı (Frontend Build)
*   **Süre:** ~1 Saat
*   **İşlem:**
    1.  `frontend/` klasöründe modern bir **React + Vite** projesi oluşturulacak.
    2.  **Sayfalar Tasarlanacak:**
        *   **Giriş Ekranı:** Şık bir Login/Register formu.
        *   **Gösterge Paneli (Dashboard):** Aktif taramaların ve geçmiş sonuçların listesi.
        *   **Yeni Görev Formu:** Hedef URL girip tarama başlatma butonu.

### Adım 3: Montaj ve Boya (Integration)
*   **Süre:** ~15 Dakika
*   **İşlem:**
    1.  Frontend ve Backend birbirine bağlanacak (CORS ayarları).
    2.  `docker-compose.yml` dosyasına Frontend servisi eklenecek, böylece tek komutla (`docker-compose up`) tüm araç çalışır hale gelecek.

## 3. Test Sürüşü
*   Sistemi ayağa kaldırıp tarayıcıdan giriş yapacağız, yeni bir tarama başlatıp sonucu ekranda göreceğiz.

**Onaylarsanız hemen Adım 1'den (Backend Auth ve User Model) başlayarak aracı toplamaya başlıyorum.**