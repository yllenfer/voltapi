from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional
from datetime import datetime
from enum import Enum

DATABASE_URL = "sqlite:///./tariffs.db"
engine = create_engine(DATABASE_URL, echo=False)


class TariffType(str, Enum):
    fixed = "fixed"
    variable = "variable"
    time_of_use = "time_of_use"


class Provider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    country: str = Field(default="ES")           # ISO country code
    region: Optional[str] = None                  # e.g. "Catalonia"
    website: Optional[str] = None
    scraper_id: str                               # matches scraper module name
    active: bool = Field(default=True)
    last_scraped: Optional[datetime] = None


class Tariff(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider.id", index=True)
    name: str                                     # e.g. "Tarifa 2.0TD"
    tariff_type: TariffType = TariffType.fixed
    kwh_price: float                              # €/kWh
    power_price: Optional[float] = None           # €/kW/year (fixed charge)
    currency: str = Field(default="EUR")
    region: Optional[str] = None
    valid_from: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: Optional[str] = None
    notes: Optional[str] = None                  # e.g. "Off-peak: 0.08 €/kWh"


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
