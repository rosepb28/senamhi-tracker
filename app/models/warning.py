"""Pydantic models for weather warnings."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import WarningSeverity, WarningStatus


class Warning(BaseModel):
    """Weather warning/alert."""

    senamhi_id: int
    warning_number: str
    department: str
    severity: WarningSeverity
    status: WarningStatus
    title: str
    description: str
    valid_from: datetime
    valid_until: datetime
    issued_at: datetime
    scraped_at: datetime = Field(default_factory=datetime.now)
