from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import Provider
from app.database import get_session
from typing import List

router = APIRouter()


@router.get("/", response_model=List[Provider])
def list_providers(session: Session = Depends(get_session)):
    """List all registered electricity providers."""
    return session.exec(select(Provider)).all()


@router.get("/{provider_id}", response_model=Provider)
def get_provider(provider_id: int, session: Session = Depends(get_session)):
    """Get a specific provider by ID."""
    provider = session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("/", response_model=Provider, status_code=201)
def create_provider(provider: Provider, session: Session = Depends(get_session)):
    """Register a new electricity provider."""
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider
