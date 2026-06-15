"""
Endesa (endesa.com) scraper.

Endesa surfaces its featured residential €/kWh on the homepage inside
elements with class `price-wrapper-price-value`. The displayed price is
the energy term (T. de energía) for the current promoted offer.
"""

import re
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapedTariff
from typing import List

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; voltapi-scraper/1.0; +https://github.com/yourusername/voltapi)"
}

URL = "https://www.endesa.com/"
PRICE_CLASS = "price-wrapper-price-value"
NUM_RE = re.compile(r"(\d+[.,]\d+)")


class EndesaScraper(BaseScraper):
    name = "endesa"

    def scrape(self) -> List[ScrapedTariff]:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        prices: List[float] = []
        for el in soup.find_all(class_=PRICE_CLASS):
            m = NUM_RE.search(el.get_text(strip=True))
            if not m:
                continue
            price = float(m.group(1).replace(",", "."))
            if 0.05 < price < 1.00:
                prices.append(price)

        if not prices:
            print("  [endesa] No prices found in .price-wrapper-price-value")
            return []

        return [ScrapedTariff(
            name="Oferta destacada (homepage)",
            kwh_price=prices[0],
            tariff_type="fixed",
            currency="EUR",
            source_url=URL,
            notes=(
                "Precio del término de energía (T. de energía) de la oferta "
                "promocionada en la portada de Endesa. Sin permanencia. "
                f"Todos los precios encontrados: {prices}"
            ),
        )]
