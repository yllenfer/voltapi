#!/usr/bin/env python3
"""
Seed the database with all built-in providers and run their scrapers.

Usage:
    python seed.py              # seed all providers
    python seed.py iberdrola    # seed only one provider (by scraper_id)
"""

import sys
from app.database import init_db, engine
from app.models import Provider
from app.scraper_runner import run_scraper
from sqlmodel import Session, select

PROVIDERS = [
    Provider(
        name="Iberdrola",
        country="ES",
        website="https://www.iberdrola.es/luz/precio-luz-hoy",
        scraper_id="iberdrola",
        active=True,
    ),
    Provider(
        name="Pepe Energy",
        country="ES",
        website="https://www.pepeenergy.com/tarifas-luz",
        scraper_id="pepe_energy",
        active=True,
    ),
    Provider(
        name="Endesa",
        country="ES",
        website="https://www.endesa.com/",
        scraper_id="endesa",
        active=True,
    ),
    # Add new providers here following the same pattern
]

init_db()

filter_id = sys.argv[1] if len(sys.argv) > 1 else None

with Session(engine) as session:
    for p in PROVIDERS:
        if filter_id and p.scraper_id != filter_id:
            continue

        existing = session.exec(
            select(Provider).where(Provider.scraper_id == p.scraper_id)
        ).first()

        if existing:
            print(f"  {p.name} already exists (id={existing.id}), skipping insert.")
            provider_id = existing.id
        else:
            session.add(p)
            session.commit()
            session.refresh(p)
            provider_id = p.id
            print(f"  Created {p.name} (id={provider_id})")

        print(f"  Running scraper: {p.scraper_id}...")
        try:
            run_scraper(p.scraper_id, provider_id)
        except Exception as e:
            print(f"  [ERROR] {e}")

print("\nDone. Visit http://localhost:8099/docs")
