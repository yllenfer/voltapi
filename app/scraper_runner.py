import importlib
import inspect
from datetime import datetime
from sqlmodel import Session, select
from app.models import Tariff, Provider
from app.database import engine
from app.scrapers.base import BaseScraper


def get_scraper(scraper_id: str) -> BaseScraper:
    """Dynamically load a scraper class by its module name."""
    module = importlib.import_module(f"app.scrapers.{scraper_id}")
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseScraper) and obj is not BaseScraper:
            if getattr(obj, "name", None) == scraper_id:
                return obj()
    raise ValueError(f"No scraper with name='{scraper_id}' found in app/scrapers/{scraper_id}.py")


def run_scraper(scraper_id: str, provider_id: int):
    scraper = get_scraper(scraper_id)
    rates = scraper.run()

    with Session(engine) as session:
        # Delete old rates for this provider before inserting fresh ones
        old = session.exec(
            select(Tariff).where(Tariff.provider_id == provider_id)
        ).all()
        for t in old:
            session.delete(t)

        for t in rates:
            session.add(Tariff(
                provider_id=provider_id,
                name=t.name,
                kwh_price=t.kwh_price,
                tariff_type=t.tariff_type,
                power_price=t.power_price,
                currency=t.currency,
                region=t.region,
                source_url=t.source_url,
                notes=t.notes,
                scraped_at=datetime.utcnow(),
            ))

        # Update provider's last_scraped timestamp
        provider = session.get(Provider, provider_id)
        if provider:
            provider.last_scraped = datetime.utcnow()
            session.add(provider)

        session.commit()
    print(f"Saved {len(rates)} rates for provider_id={provider_id}")


def run_all_scrapers():
    """Run all active scrapers. Called by the scheduler."""
    with Session(engine) as session:
        providers = session.exec(
            select(Provider).where(Provider.active == True)
        ).all()

    for provider in providers:
        try:
            run_scraper(provider.scraper_id, provider.id)
        except Exception as e:
            print(f"[ERROR] Scraper '{provider.scraper_id}' failed: {e}")
