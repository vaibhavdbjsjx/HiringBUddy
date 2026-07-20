from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from db_models import SystemSettings
from schemas import SettingsResponse, SettingsUpdate

router = APIRouter()

def get_or_create_settings(db: Session):
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    return settings

@router.put("/", response_model=SettingsResponse)
def update_settings(update_data: SettingsUpdate, db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    if update_data.smtp_email is not None:
        settings.smtp_email = update_data.smtp_email
    if update_data.smtp_password is not None:
        settings.smtp_password = update_data.smtp_password
    if update_data.sender_name is not None:
        settings.sender_name = update_data.sender_name
    if update_data.company_name is not None:
        settings.company_name = update_data.company_name
    if update_data.invite_template is not None:
        settings.invite_template = update_data.invite_template
    if update_data.reject_template is not None:
        settings.reject_template = update_data.reject_template
    if update_data.shortlist_template is not None:
        settings.shortlist_template = update_data.shortlist_template
    db.commit()
    db.refresh(settings)
    return settings
