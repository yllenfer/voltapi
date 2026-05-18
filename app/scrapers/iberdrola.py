"""
Iberdrola scraper — two data sources:

1. Static HTML: Plan Online flat rate + power charges (BeautifulSoup)
2. REE public API (esios.ree.es): PVPC hourly prices for the regulated market

REE's ESIOS API is the same source Iberdrola uses for their hourly chart.
No API key needed for the public endpoint used here.
"""

import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapedTariff
from typing import List

IBERDROLA_URL = "https://www.iberdrola.es/luz/precio-luz-hoy"

# REE ESIOS public endpoint — indicator 1001 = PVPC (mercado regulado)
# Returns hourly prices for a given date in €/MWh (we convert to €/kWh)
REE_API_URL = "https://api.esios.ree.es/indicators/1001"


class IberdrolaScraper(BaseScraper):
    name = "iberdrola"

    def scrape(self) -> List[ScrapedTariff]:
        tariffs = []

        tariffs.extend(self._scrape_static_plans())
        tariffs.extend(self._scrape_pvpc_today())

        return tariffs

    # ── Plan Online & power charges from static HTML ──────────────────────

    def _scrape_static_plans(self) -> List[ScrapedTariff]:
        tariffs = []
        try:
            resp = requests.get(
                IBERDROLA_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; tariff-scraper/1.0)"},
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Plan Online flat rate — appears in the pricing section
            # The price is embedded as text: "0,109420 €/kWh" or "0.1199 €/kWh"
            # We search all text nodes for the pattern
            import re
            price_pattern = re.compile(r"(\d+[.,]\d+)\s*€/kWh")

            found_prices = set()
            for tag in soup.find_all(string=price_pattern):
                match = price_pattern.search(tag)
                if match:
                    price_str = match.group(1).replace(",", ".")
                    price = float(price_str)
                    if price not in found_prices and 0.05 < price < 0.50:
                        found_prices.add(price)

            # Plan Online is the fixed flat rate (usually lowest, ~0.109-0.12)
            # Mercado regulado yearly average is also present
            # We extract both if found
            prices_sorted = sorted(found_prices)

            if prices_sorted:
                tariffs.append(ScrapedTariff(
                    name="Plan Online (tarifa plana)",
                    kwh_price=prices_sorted[0],  # lowest = fixed plan
                    tariff_type="fixed",
                    currency="EUR",
                    source_url=IBERDROLA_URL,
                    notes="Precio fijo 24h, sin permanencia",
                ))

            if len(prices_sorted) > 1:
                tariffs.append(ScrapedTariff(
                    name="Mercado Regulado (media anual)",
                    kwh_price=prices_sorted[-1],  # higher = regulated market avg
                    tariff_type="variable",
                    currency="EUR",
                    source_url=IBERDROLA_URL,
                    notes="PVPC - precio medio del año (mercado regulado REE)",
                ))

        except Exception as e:
            print(f"  [iberdrola] Static HTML scrape failed: {e}")

        return tariffs

    # ── PVPC hourly prices from REE ESIOS API ────────────────────────────

    def _scrape_pvpc_today(self) -> List[ScrapedTariff]:
        tariffs = []
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            params = {
                "start_date": f"{today}T00:00:00Z",
                "end_date": f"{today}T23:59:59Z",
            }
            headers = {
                "Accept": "application/json; application/vnd.esios-api-v1+json",
                "Content-Type": "application/json",
                "Host": "api.esios.ree.es",
            }
            resp = requests.get(REE_API_URL, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            values = data.get("indicator", {}).get("values", [])
            if not values:
                print("  [iberdrola] REE API returned no hourly values")
                return tariffs

            # Each value: {"value": 154.79, "datetime": "2026-05-18T22:00:00Z", ...}
            # Value is in €/MWh — convert to €/kWh by dividing by 1000
            hourly_prices = []
            for v in values:
                mwh_price = v.get("value", 0)
                kwh_price = round(mwh_price / 1000, 6)
                hour_str = v.get("datetime", "")
                hourly_prices.append((hour_str, kwh_price))

            if hourly_prices:
                prices_only = [p for _, p in hourly_prices]
                avg = round(sum(prices_only) / len(prices_only), 6)
                min_price = min(prices_only)
                max_price = max(prices_only)
                cheapest_hour = min(hourly_prices, key=lambda x: x[1])

                tariffs.append(ScrapedTariff(
                    name="PVPC Hoy (media horaria)",
                    kwh_price=avg,
                    tariff_type="time_of_use",
                    currency="EUR",
                    source_url=REE_API_URL,
                    notes=(
                        f"Mín: {min_price} €/kWh | "
                        f"Máx: {max_price} €/kWh | "
                        f"Hora más barata: {cheapest_hour[0][11:16]}Z ({cheapest_hour[1]} €/kWh)"
                    ),
                ))

        except Exception as e:
            print(f"  [iberdrola] REE API scrape failed: {e}")

        return tariffs
