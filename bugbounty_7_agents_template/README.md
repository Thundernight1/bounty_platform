# BugBounty 7-Agent Otomasyon Şablonu (TR)

Bu repo, **tek bir bug bounty programı** üzerinde **7 alt ajanı** paralel çalıştırıp,
çıktıları birleştirerek rapor üreten bir akış sağlar. %80–90 otomatik, **son %10 manuel onay** kapısı vardır.


## Ajanlar
1. **envanter** – Domain/alt alan listesi ve temel varlık envanteri
2. **tech_fp** – Teknoloji fingerprint (server headers, çatı, CDN vb.)
3. **scan_web** – Pasif/zararsız HTTP kontrolleri + (varsa) nuclei ile bilinen imzalar
4. **content** – İçerik keşfi (düşük etkili wordlist, robots.txt, common paths)
5. **auth** – Oturum/çerez/başlık kontrolleri (pasif; brute/DoS yok)
6. **prompt_ai** – LLM endpoint’lerine prompt‑injection güvenlik kontrolleri (isteğe bağlı)
7. **reporter** – Bulguları birleştirir, **MANUEL ONAY** bekler, özet raporu üretir

## Hızlı Kurulum
- Gereksinimler: Python 3.10+, `pip`, (opsiyonel) `subfinder`, `httpx` (ProjectDiscovery), `nuclei`, `ffuf`
- Kurulum:
```bash
pip install -r requirements.txt
```
- Yapılandırma dosyasını düzenle: `configs/program.yaml`
- Çalıştır:
```bash
python agents/coordinator.py --program configs/program.yaml
```

### Manuel Onay Kapısı
Rapor üretimi öncesi **outputs/REVIEW.md** oluşur. İncele ve onay için:
```bash
echo "OK" > outputs/APPROVED.txt
```
Sonrasında rapor finalize edilir: `outputs/report.md`, `outputs/report.json`

## Dosya Yapısı
```
agents/
  coordinator.py
  utils.py
  envanter.py
  tech_fp.py
  scan_web.py
  content.py
  auth_checks.py
  prompt_ai.py
  reporter.py
configs/
  program.yaml
data/
  prompt_payloads.txt
outputs/           # otomatik oluşur
requirements.txt
README.md
```

## Notlar
- Dış araçlar yoksa ajanlar **zararsız HTTP tabanlı** fallback moduna geçer.
- `prompt_ai` ajanı, `configs/program.yaml` içindeki `llm_endpoints` listesine göre çalışır.
- Hız/Risk limitleri `program.yaml` içindeki `rate_limit` ve `allowed_tests` ile kontrol edilir.
