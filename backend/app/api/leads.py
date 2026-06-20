import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.contact import Contact
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadOut

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)) -> Lead:
    contact = (
        await db.execute(select(Contact).where(Contact.email == payload.email))
    ).scalar_one_or_none()
    if contact is None:
        contact = Contact(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
        )
        db.add(contact)
        await db.flush()

    lead = Lead(contact_id=contact.id, source=payload.source, score=payload.score)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Lead:
    lead = await db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
