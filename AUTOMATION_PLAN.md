# 🤖 %90 Otomatik + %10 Manuel Sistem

## 🎯 WORKFLOW

### Gece 00:00 (Tamamen Otomatik) 🌙

```
┌─────────────────────────────────────────┐
│  CRON JOB BAŞLAR                        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  1. HackerOne API                       │
│     - Aktif 20 program çek              │
│     - In-scope domain'leri parse et     │
│     - Son 7 gün içinde taranmamışları al│
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  2. Her Program İçin:                   │
│     ├─ envanter.py → Subdomains         │
│     ├─ tech_fp.py → Headers             │
│     ├─ scan_web.py → Nuclei CVEs        │
│     ├─ content.py → Hidden paths        │
│     ├─ auth_checks.py → Security headers│
│     ├─ prompt_ai.py → LLM injection     │
│     └─ 5-10 dakika/program              │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  3. Filtre & Skorlama (Otomatik)        │
│     ✓ Duplicate kontrolü                │
│     ✓ Severity hesaplama                │
│     ✓ Confidence scoring                │
│     ✓ Low-hanging fruit öncelik         │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  4. Report Draft Oluştur                │
│     - HackerOne formatında              │
│     - Screenshot'lar hazırla            │
│     - PoC curl komutları                │
│     - CVSS skoru                        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  5. REVIEW.md Oluştur                   │
│     outputs/daily_review_2025-01-24.md  │
│     + Telegram/Email bildirim GÖNDER    │
└─────────────────────────────────────────┘
```

### Sabah 08:00 (Manuel Review) ☕

```
┌─────────────────────────────────────────┐
│  TELEGRAM MESAJI                        │
│  "🎯 12 yeni bug bulundu!               │
│   - 3 High severity                     │
│   - 7 Medium severity                   │
│   - 2 Low severity                      │
│   Review: /app/outputs/review.md"       │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  SEN REVIEW YAPIYORSUN                  │
│  outputs/daily_review_2025-01-24.md     │
│                                          │
│  Bug #1: ✅ APPROVE                     │
│  Bug #2: ⏭️ SKIP (duplicate)            │
│  Bug #3: ✏️ EDIT (detay ekle)           │
│  ...                                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  python approve.py                      │
│  - APPROVED.txt'deki bug'ları gönder    │
│  - Rate limiting (saatte 2 rapor)       │
│  - Success/fail log                     │
└─────────────────────────────────────────┘
```

---

## 📋 DOSYA YAPISI

```
bounty_platform/
├── automation/
│   ├── scheduler.py           # Ana orchestrator
│   ├── hackerone_api.py       # HackerOne API wrapper
│   ├── bugcrowd_api.py        # Bugcrowd API (future)
│   ├── filter_engine.py       # Duplicate & scoring
│   ├── report_generator.py    # Report template engine
│   └── notifier.py            # Telegram/Email bildirim
│
├── templates/
│   ├── hackerone_report.md    # HackerOne formatı
│   ├── bugcrowd_report.md     # Bugcrowd formatı
│   └── review_template.md     # Daily review formatı
│
├── database/
│   ├── findings.db            # Gönderilen raporlar
│   └── programs.db            # Program history
│
├── outputs/
│   ├── daily_review_2025-01-24.md
│   ├── APPROVED.txt           # Sen approve ettiklerini buraya yazarsın
│   └── reports/
│       ├── bug_001.md
│       ├── bug_002.md
│       └── ...
│
└── bugbounty_7_agents_template/  # Mevcut ajanlar
    └── agents/
```

---

## 🔧 YENİ BILEŞENLER

### 1. `automation/scheduler.py`

```python
#!/usr/bin/env python3
"""
Ana orchestrator - Her gece 00:00 çalışır
"""
import asyncio
import schedule
import time
from datetime import datetime
from hackerone_api import get_active_programs
from filter_engine import should_scan, is_duplicate
from notifier import send_telegram

async def nightly_scan():
    """Her gece çalışacak ana fonksiyon"""
    print(f"[{datetime.now()}] Nightly scan başladı...")

    # 1. Programları çek
    programs = await get_active_programs(limit=20)

    findings = []
    for program in programs:
        # Daha önce tarandı mı?
        if not should_scan(program):
            continue

        # 7-ajan sistemini çalıştır
        result = await run_agents_for_program(program)

        # Filtreleme
        for bug in result['bugs']:
            if not is_duplicate(program, bug):
                findings.append(bug)

    # 2. Review dosyası oluştur
    create_review_file(findings)

    # 3. Bildirim gönder
    await send_telegram(
        f"🎯 {len(findings)} yeni bug bulundu!\n"
        f"Review: /app/outputs/daily_review_{datetime.now().date()}.md"
    )

async def run_agents_for_program(program):
    """Bir program için 7 ajanı çalıştır"""
    from bugbounty_7_agents_template.agents import coordinator

    # Config oluştur
    config = {
        'program_name': program['name'],
        'targets': [{'domain': d, 'in_scope': True}
                    for d in program['domains']],
        'rate_limit': {'rps': 2, 'max_concurrency': 5},
        'allowed_tests': {
            'passive_http': True,
            'content_discovery': True,
            'nuclei_signatures': True,
            'auth_header_checks': True,
            'prompt_injection_checks': False  # Riskli
        }
    }

    # Coordinator çalıştır (auto-approve mode)
    await coordinator.main(config, auto_approve=True)

    # Sonuçları parse et
    return parse_agent_outputs()

def create_review_file(findings):
    """Manuel review için dosya oluştur"""
    with open(f"outputs/daily_review_{datetime.now().date()}.md", "w") as f:
        f.write("# Daily Bug Bounty Review\n\n")
        f.write(f"**Date**: {datetime.now()}\n")
        f.write(f"**Total Findings**: {len(findings)}\n\n")

        for i, bug in enumerate(findings, 1):
            f.write(f"## Bug #{i}\n\n")
            f.write(f"**Program**: {bug['program']}\n")
            f.write(f"**Type**: {bug['type']}\n")
            f.write(f"**Severity**: {bug['severity']}\n")
            f.write(f"**Confidence**: {bug['confidence']}\n")
            f.write(f"**Estimated Bounty**: ${bug['estimated_bounty']}\n\n")
            f.write(f"**Details**:\n{bug['description']}\n\n")
            f.write(f"**Action**: [ ] APPROVE  [ ] SKIP  [ ] EDIT\n")
            f.write(f"**Report**: `outputs/reports/bug_{i:03d}.md`\n\n")
            f.write("---\n\n")

# Schedule
schedule.every().day.at("00:00").do(lambda: asyncio.run(nightly_scan()))

if __name__ == "__main__":
    print("🤖 Bug Bounty Automation başlatıldı...")
    print("⏰ Her gece 00:00'da tarama yapılacak")

    while True:
        schedule.run_pending()
        time.sleep(60)
```

---

### 2. `automation/hackerone_api.py`

```python
"""
HackerOne API wrapper
Docs: https://api.hackerone.com/docs/v1
"""
import os
import aiohttp
import asyncio

HACKERONE_API_USER = os.getenv("HACKERONE_API_USER")
HACKERONE_API_TOKEN = os.getenv("HACKERONE_API_TOKEN")

async def get_active_programs(limit=20):
    """
    Aktif bug bounty programlarını çek

    Returns:
        List[Dict]: Program listesi
    """
    url = "https://api.hackerone.com/v1/hackers/programs"

    auth = aiohttp.BasicAuth(HACKERONE_API_USER, HACKERONE_API_TOKEN)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as resp:
            data = await resp.json()

            programs = []
            for program in data['data'][:limit]:
                # Parse et
                programs.append({
                    'id': program['id'],
                    'name': program['attributes']['handle'],
                    'domains': extract_domains(program),
                    'min_bounty': program['attributes'].get('minimum_bounty_amount', 0),
                    'avg_bounty': program['attributes'].get('average_bounty_amount', 0)
                })

            return programs

def extract_domains(program):
    """Program'dan in-scope domain'leri çıkar"""
    domains = []
    for scope in program['relationships']['structured_scopes']['data']:
        if scope['attributes']['asset_type'] == 'URL':
            domain = scope['attributes']['asset_identifier']
            if scope['attributes']['eligible_for_bounty']:
                domains.append(domain)
    return domains

async def submit_report(program_id, vulnerability):
    """
    Bug raporu gönder

    Args:
        program_id: Program ID
        vulnerability: Bug detayları
    """
    url = f"https://api.hackerone.com/v1/reports"

    auth = aiohttp.BasicAuth(HACKERONE_API_USER, HACKERONE_API_TOKEN)

    payload = {
        "data": {
            "type": "report",
            "attributes": {
                "team_handle": program_id,
                "title": vulnerability['title'],
                "vulnerability_information": vulnerability['description'],
                "severity_rating": vulnerability['severity'],
                "impact": vulnerability['impact']
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, auth=auth) as resp:
            if resp.status == 201:
                report = await resp.json()
                return {
                    'success': True,
                    'report_id': report['data']['id'],
                    'url': f"https://hackerone.com/reports/{report['data']['id']}"
                }
            else:
                return {'success': False, 'error': await resp.text()}
```

---

### 3. `automation/filter_engine.py`

```python
"""
Bug filtreleme ve skorlama
"""
import sqlite3
from datetime import datetime, timedelta

def should_scan(program):
    """Bu program taranmalı mı?"""
    conn = sqlite3.connect('database/programs.db')
    cursor = conn.execute(
        "SELECT last_scan FROM programs WHERE name=?",
        (program['name'],)
    )
    row = cursor.fetchone()

    # Hiç taranmamış
    if not row:
        return True

    # Son 7 gün içinde taranmış mı?
    last_scan = datetime.fromisoformat(row[0])
    return (datetime.now() - last_scan).days >= 7

def is_duplicate(program, bug):
    """Bu bug daha önce gönderildi mi?"""
    conn = sqlite3.connect('database/findings.db')
    cursor = conn.execute(
        "SELECT * FROM findings WHERE program=? AND url=? AND type=?",
        (program['name'], bug['url'], bug['type'])
    )
    return cursor.fetchone() is not None

def calculate_score(bug):
    """
    Bug öncelik skoru hesapla

    Returns:
        int: 0-100 arası skor
    """
    score = 0

    # Severity
    severity_scores = {
        'critical': 40,
        'high': 30,
        'medium': 20,
        'low': 10
    }
    score += severity_scores.get(bug['severity'], 0)

    # Confidence (tool'un ne kadar emin olduğu)
    if bug.get('confidence') == 'high':
        score += 30
    elif bug.get('confidence') == 'medium':
        score += 20
    else:
        score += 10

    # Low-hanging fruit bonus (hızlı kabul edilir)
    if bug['type'] in ['missing_csp', 'cors_misconfiguration', 'subdomain_takeover']:
        score += 20

    # Proof-of-concept var mı?
    if bug.get('poc'):
        score += 10

    return min(score, 100)

def estimate_bounty(bug, program):
    """Tahmini bounty hesapla"""
    base_amounts = {
        'critical': 500,
        'high': 200,
        'medium': 50,
        'low': 20
    }

    base = base_amounts.get(bug['severity'], 0)

    # Program'ın avg bounty'sine göre ayarla
    if program.get('avg_bounty'):
        multiplier = program['avg_bounty'] / 200  # 200 default avg
        base *= multiplier

    return int(base)
```

---

### 4. `automation/notifier.py`

```python
"""
Bildirim sistemi (Telegram/Email)
"""
import os
import aiohttp

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram(message):
    """Telegram'a bildirim gönder"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return resp.status == 200

async def send_email(subject, body):
    """Email gönder (opsiyonel)"""
    # SMTP implementasyonu
    pass
```

---

### 5. `approve.py` (Manuel Approval Script)

```python
#!/usr/bin/env python3
"""
Manuel approval sonrası raporları gönder
"""
import asyncio
from automation.hackerone_api import submit_report

async def process_approvals():
    """APPROVED.txt'deki bug'ları gönder"""

    with open("outputs/APPROVED.txt", "r") as f:
        approved_ids = [line.strip() for line in f if line.strip()]

    for bug_id in approved_ids:
        # Report'u yükle
        with open(f"outputs/reports/bug_{bug_id}.md", "r") as f:
            report_content = f.read()

        # Parse et ve gönder
        vulnerability = parse_report(report_content)
        result = await submit_report(vulnerability['program'], vulnerability)

        if result['success']:
            print(f"✅ Bug {bug_id} gönderildi: {result['url']}")
            # Database'e kaydet
            save_to_db(bug_id, result)
        else:
            print(f"❌ Bug {bug_id} gönderilemedi: {result['error']}")

        # Rate limiting (saatte 2 rapor)
        await asyncio.sleep(1800)  # 30 dakika bekle

if __name__ == "__main__":
    asyncio.run(process_approvals())
```

---

## 🚀 KULLANIM

### İlk Kurulum

```bash
# 1. Dependencies
pip install schedule aiohttp aiogram python-dotenv

# 2. Environment variables
cat > .env << EOF
HACKERONE_API_USER=your_username
HACKERONE_API_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EOF

# 3. Database setup
python -c "from automation.setup_db import init; init()"

# 4. Test run
python automation/scheduler.py --test
```

### Günlük Kullanım

#### Gece (Otomatik):
- Sistem kendi başına çalışıyor
- 00:00'da tara başlıyor
- Sabah Telegram'dan bildirim geliyor

#### Sabah (Manuel):
```bash
# 1. Review dosyasını aç
vim outputs/daily_review_2025-01-24.md

# 2. Approve etmek istediklerini APPROVED.txt'ye ekle
echo "bug_001" >> outputs/APPROVED.txt
echo "bug_003" >> outputs/APPROVED.txt
echo "bug_007" >> outputs/APPROVED.txt

# 3. Edit gerekenleri düzenle
vim outputs/reports/bug_002.md

# 4. Gönder
python approve.py
```

---

## ⚙️ YAPILANDIRMA

### `config/automation.yaml`

```yaml
scheduler:
  scan_time: "00:00"
  max_programs_per_night: 20
  max_reports_per_day: 10

filtering:
  min_confidence: medium
  min_severity: medium
  ignore_types:
    - ssl_certificate
    - spf_dkim_dmarc

  priority_types:
    - missing_csp
    - cors_misconfiguration
    - subdomain_takeover
    - open_redirect

notifications:
  telegram: true
  email: false
  desktop: false

rate_limiting:
  reports_per_hour: 2
  requests_per_minute: 10
```

---

## 📊 EKLENTİLER

### Dashboard (Opsiyonel)

```bash
# Basit web dashboard
python -m http.server 8080 --directory outputs/
```

Browser'da: http://localhost:8080

Görebilirsin:
- Günlük review dosyaları
- Gönderilen raporlar
- İstatistikler

---

## 🎯 ÖZET

| Adım | Otomasyon % | Manuel % |
|------|-------------|----------|
| Program seçme | 100% | 0% |
| Tarama | 100% | 0% |
| Filtreleme | 90% | 10% |
| Report oluşturma | 100% | 0% |
| **Review & Approval** | **0%** | **100%** |
| Rapor gönderme | 100% | 0% |
| **TOPLAM** | **~85-90%** | **10-15%** |

**Senin İş Yükün**: Günde 10-15 dakika review

**Sistem İş Yükü**: 7/24 tarama ve analiz

---

Bu yapı sana uygun mu? Yoksa daha farklı bir şey mi hayal ediyordun?
