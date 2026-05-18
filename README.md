# ⚡ VoltAPI

> A self-hosted, open source REST API that adds electricity tariff data from providers worldwide. Designed for Home Assistant and other smart home integrations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![OpenAPI](https://img.shields.io/badge/docs-OpenAPI%203.0-blue)](https://your-deploy-url/docs)

---

## Why VoltAPI?

Most smart home setups (Home Assistant, openHAB, etc.) require you to **manually hardcode your electricity rate**. VoltAPI scrapes provider websites automatically so your energy dashboards always reflect real current pricing — without touching a config file.

## Providers included

| Country | Provider | Tariff Types | Scraper |
|---------|----------|-------------|---------|
| 🇪🇸 Spain | Iberdrola | Fixed (Plan Online), PVPC hourly | `iberdrola` |
| 🇪🇸 Spain | Pepe Energy | Fixed (6-month), Variable (ECO) | `pepe_energy` |
| — | Your provider | — | [Add it! →](CONTRIBUTING.md) |

**Want to add your country's providers? See [CONTRIBUTING.md](CONTRIBUTING.md) — it takes ~30 lines of Python.**

---

## Quick Start

```bash
git clone https://github.com/yourusername/voltapi.git
cd voltapi

# Start the API
docker compose up -d

# Seed with Spanish providers
python seed.py

# Open Swagger UI
open http://localhost:8099/docs
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tariffs` | All tariffs (filterable by provider, region, max price) |
| `GET` | `/tariffs/cheapest` | Cheapest tariff available |
| `GET` | `/tariffs/{id}` | Single tariff |
| `POST` | `/tariffs/refresh/{provider_id}` | Manually re-scrape a provider |
| `GET` | `/providers` | All registered providers |
| `GET` | `/providers/{id}` | Single provider |
| `POST` | `/providers` | Register a new provider |
| `GET` | `/docs` | Swagger UI (interactive) |
| `GET` | `/redoc` | ReDoc documentation |
| `GET` | `/health` | Health check |

## Home Assistant Integration

```yaml
# configuration.yaml
sensor:
  - platform: rest
    name: "Electricity Price (cheapest)"
    resource: http://YOUR_SERVER_IP:8099/tariffs/cheapest
    value_template: "{{ value_json.kwh_price }}"
    unit_of_measurement: "EUR/kWh"
    scan_interval: 3600

  - platform: rest
    name: "Iberdrola PVPC Today"
    resource: http://YOUR_SERVER_IP:8099/tariffs?provider_id=1
    json_attributes_path: "$[0]"
    json_attributes:
      - kwh_price
      - notes
      - scraped_at
    value_template: "{{ value_json[0].kwh_price }}"
    unit_of_measurement: "EUR/kWh"
    scan_interval: 3600
```

## Deployment options

**Local / Home Lab (recommended for HA users)**
```bash
docker compose up -d
```

**Render / Railway (free public instance)**
- Connect your GitHub fork
- Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Deploy — done

**SwaggerHub** (docs only)
- Export `/openapi.json` from your running instance
- Import into SwaggerHub for hosted, shareable documentation

## Tech Stack

- **FastAPI** — REST API + built-in Swagger/ReDoc UI
- **SQLModel** — ORM with SQLite (zero-config)
- **BeautifulSoup4** — static HTML scraping
- **Playwright** — JS-rendered page scraping
- **REE ESIOS API** — Spain's public electricity data source
- **APScheduler** — automatic re-scraping every 6 hours
- **Docker** — containerised deployment

## License

MIT — do whatever you want, attribution appreciated.
