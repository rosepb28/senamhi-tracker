"""Pydantic models for weather warnings."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WarningSeverity(str, Enum):
    """Warning severity levels."""

    GREEN = "verde"
    YELLOW = "amarillo"
    ORANGE = "naranja"
    RED = "rojo"


class WarningStatus(str, Enum):
    """Warning status."""

    EMITIDO = "emitido"
    VIGENTE = "vigente"
    VENCIDO = "vencido"


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
