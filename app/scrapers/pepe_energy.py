"""
Pepe Energy (pepeenergy.com) scraper.

Pepe Energy publishes rates on static HTML pages — no JS rendering needed.
They offer two main tariff types:
  - Tarifa Fija: fixed flat rate, reviewed every 6 months
  - Tarifa Variable (ECO): monthly variable rate tied to wholesale market

Prices on the site include IVA 10% + Impuesto Eléctrico 0.5% for residential <10kW.
We scrape the displayed price (taxes included) for ease of comparison.

Source pages:
  https://www.pepeenergy.com/tarifas-luz/tarifa-fija-luz
  https://www.pepeenergy.com/tarifas-luz/tarifa-variable-luz
"""

import re
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapedTariff
from typing import List

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; voltapi-scraper/1.0; +https://github.com/yourusername/voltapi)"
}

FIXED_URL = "https://www.pepeenergy.com/tarifas-luz/tarifa-fija-luz"
VARIABLE_URL = "https://www.pepeenergy.com/tarifas-luz/tarifa-variable-luz"

PRICE_RE = re.compile(r"(\d+[.,]\d+)\s*€/kWh")


def _extract_prices(url: str) -> List[float]:
    """Fetch a page and return all €/kWh values found in the HTML."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    found = set()
    for tag in soup.find_all(string=PRICE_RE):
        for match in PRICE_RE.finditer(tag):
            price = float(match.group(1).replace(",", "."))
            if 0.05 < price < 1.00:  # sanity range for €/kWh
                found.add(price)

    return sorted(found)


class PepeEnergyScraper(BaseScraper):
    name = "pepe_energy"

    def scrape(self) -> List[ScrapedTariff]:
        rates = []

        # ── Tarifa Fija ──────────────────────────────────────────────────
        try:
            prices = _extract_prices(FIXED_URL)
            if prices:
                # The main advertised price is typically the lowest on the page
                # (mainland peninsula, residential <10kW, IVA 10% + IE 0.5%)
                rates.append(ScrapedTariff(
                    name="Tarifa Fija (precio plano 6 meses)",
                    kwh_price=prices[0],
                    tariff_type="fixed",
                    currency="EUR",
                    source_url=FIXED_URL,
                    notes=(
                        "Precio fijo durante 6 meses, sin permanencia. "
                        "Incluye IVA 10% + Impuesto Eléctrico 0.5%. "
                        "Cuota mensual de 4€ adicional. "
                        f"Todas las tarifas en página: {prices}"
                    ),
                ))
        except Exception as e:
            print(f"  [pepe_energy] Tarifa Fija scrape failed: {e}")

        # ── Tarifa Variable (ECO) ────────────────────────────────────────
        try:
            prices = _extract_prices(VARIABLE_URL)
            if prices:
                rates.append(ScrapedTariff(
                    name="Tarifa Variable ECO (precio mensual)",
                    kwh_price=prices[0],
                    tariff_type="variable",
                    currency="EUR",
                    source_url=VARIABLE_URL,
                    notes=(
                        "Precio varía cada mes según mercado mayorista. "
                        "3 tramos horarios: Punta / Llano / Valle. "
                        "Incluye IVA 10% + Impuesto Eléctrico 0.5%. "
                        "Cuota mensual de 4€ adicional. "
                        f"Precios en página: {prices}"
                    ),
                ))
        except Exception as e:
            print(f"  [pepe_energy] Tarifa Variable scrape failed: {e}")

        return rates
