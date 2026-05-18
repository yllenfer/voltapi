from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScrapedTariff:
    """Normalized output that every scraper must produce."""
    name: str
    kwh_price: float
    tariff_type: str = "fixed"       # fixed | variable | time_of_use
    power_price: float | None = None
    currency: str = "EUR"
    region: str | None = None
    source_url: str | None = None
    notes: str | None = None


class BaseScraper(ABC):
    """
    All provider scrapers must inherit from this class.

    Steps to add a new provider:
    1. Create app/scrapers/<provider_name>.py
    2. Subclass BaseScraper
    3. Implement the `scrape()` method to return List[ScrapedTariff]
    4. Register the provider in the DB with scraper_id matching the filename
    """

    name: str = "base"

    @abstractmethod
    def scrape(self) -> List[ScrapedTariff]:
        """Scrape and return a list of normalised tariffs."""
        ...

    def run(self) -> List[ScrapedTariff]:
        print(f"[{datetime.utcnow().isoformat()}] Running scraper: {self.name}")
        results = self.scrape()
        print(f"  → Found {len(results)} tariff(s)")
        return results
