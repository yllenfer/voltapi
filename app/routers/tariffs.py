from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.models import Tariff, Provider
from app.database import get_session
from app.scraper_runner import run_scraper
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[Tariff])
def list_tariffs(
    provider_id: Optional[int] = Query(None, description="Filter by provider"),
    region: Optional[str] = Query(None, description="Filter by region"),
    max_kwh_price: Optional[float] = Query(None, description="Max €/kWh"),
    session: Session = Depends(get_session),
):
    """
    List current electricity tariffs.

    Use this endpoint in Home Assistant as a REST sensor to get live pricing.
    """
    query = select(Tariff)
    if provider_id:
        query = query.where(Tariff.provider_id == provider_id)
    if region:
        query = query.where(Tariff.region == region)
    if max_kwh_price:
        query = query.where(Tariff.kwh_price <= max_kwh_price)
    return session.exec(query).all()


@router.get("/cheapest", response_model=Tariff)
def cheapest_tariff(
    region: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """Return the cheapest available tariff, optionally filtered by region."""
    query = select(Tariff).order_by(Tariff.kwh_price)
    if region:
        query = query.where(Tariff.region == region)
    tariff = session.exec(query).first()
    if not tariff:
        raise HTTPException(status_code=404, detail="No tariffs found")
    return tariff


@router.get("/{tariff_id}", response_model=Tariff)
def get_tariff(tariff_id: int, session: Session = Depends(get_session)):
    """Get a specific tariff by ID."""
    tariff = session.get(Tariff, tariff_id)
    if not tariff:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return tariff


@router.post("/refresh/{provider_id}", status_code=202)
def refresh_provider_tariffs(
    provider_id: int, session: Session = Depends(get_session)
):
    """Manually trigger a re-scrape for a specific provider."""
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    run_scraper(provider.scraper_id, provider_id)
    return {"message": f"Scrape triggered for {provider.name}"}
