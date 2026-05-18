# Contributing to VoltAPI

First off — thank you! The more providers we have, the more useful this is for everyone.

## The fastest way to contribute: add a provider scraper

A scraper is just a Python class. Here's everything you need to know.

### 1. Check if your provider is already in progress

Look through [open issues](https://github.com/yourusername/voltapi/issues) and [open PRs](https://github.com/yourusername/voltapi/pulls) before starting — someone may already be working on it.

If not, [open an issue](https://github.com/yourusername/voltapi/issues/new?template=new_provider.md) to claim it so there's no duplicate work.

### 2. Create your scraper file

Create `app/scrapers/<provider_slug>.py`. The slug should be lowercase with underscores: `octopus_energy`, `edf_france`, `bg_bulgaria`, etc.

```python
"""
<Provider Name> (<country>) scraper.

Source: <URL you're scraping>
Notes: <anything useful — e.g. "updates monthly", "requires Playwright", "pulls from public API">
"""

import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapedTariff
from typing import List

SOURCE_URL = "https://provider.com/pricing"

class MyProviderScraper(BaseScraper):
    name = "my_provider"   # must match the filename exactly

    def scrape(self) -> List[ScrapedTariff]:
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.raise_for_status()
        # ... parse the page ...
        return [
            ScrapedTariff(
                name="Standard Tariff",
                kwh_price=0.24,          # required: price per kWh
                tariff_type="fixed",     # fixed | variable | time_of_use
                currency="GBP",          # ISO 4217
                source_url=SOURCE_URL,
                notes="Includes VAT 5%",
            )
        ]
```

### 3. The `ScrapedTariff` fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | str | ✅ | Human-readable tariff name |
| `kwh_price` | float | ✅ | Price per kWh in `currency` |
| `tariff_type` | str | | `fixed`, `variable`, or `time_of_use` |
| `power_price` | float | | Standing/capacity charge (€/kW/day or /year) |
| `currency` | str | | ISO 4217 code (default: `EUR`) |
| `region` | str | | Region/state if price varies geographically |
| `source_url` | str | | The exact URL you scraped |
| `notes` | str | | Tax inclusion, caveats, time periods, etc. |

### 4. Add a seed entry

Add your provider to `seed.py`:

```python
Provider(
    name="My Provider",
    country="GB",           # ISO 3166-1 alpha-2
    region=None,            # or e.g. "England", "Catalonia"
    website="https://provider.com",
    scraper_id="my_provider",   # matches your filename
    active=True,
)
```

### 5. Test it locally

```bash
# Install deps
pip install -r requirements.txt

# Run just your scraper
python -c "
from app.scrapers.my_provider import MyProviderScraper
for t in MyProviderScraper().run():
    print(t)
"
```

### 6. Open a Pull Request

Include in your PR description:
- Which provider and country
- The source URL(s) you're scraping
- Whether prices include tax or not
- How often the provider updates prices (hourly / monthly / on demand)
- Any known limitations (e.g. "only works for mainland, not islands")

---

## Scraping patterns

### Pattern A — Static HTML (simplest)

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(URL, headers={"User-Agent": "voltapi/1.0"}, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")
price = soup.select_one(".price-element").get_text(strip=True)
```

### Pattern B — JS-rendered page

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle")
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")
```

### Pattern C — Public API (best if available)

```python
import requests

# Many providers (especially in Spain) pull from REE's ESIOS public API
resp = requests.get(
    "https://api.esios.ree.es/indicators/1001",
    params={"start_date": "...", "end_date": "..."},
    headers={"Accept": "application/json"},
)
data = resp.json()
```

### Pattern D — PDF tariff document

```python
import pdfplumber, io, requests

resp = requests.get(PDF_URL, timeout=20)
with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            # parse rows
```

---

## Reporting bugs or bad data

If a scraper is returning wrong prices, [open an issue](https://github.com/yourusername/voltapi/issues/new?template=bad_data.md) with:
- Provider name
- What the scraper returned
- What the provider's website actually shows
- The URL and date you checked

---

## Other ways to contribute

- **Improve existing scrapers** — better selectors, handle edge cases, add more tariff types
- **Add tests** — `tests/scrapers/test_<provider>.py` with mocked HTML responses
- **Improve the API** — filtering, pagination, rate history, comparison endpoints
- **Docs** — fix typos, add examples, translate to other languages
