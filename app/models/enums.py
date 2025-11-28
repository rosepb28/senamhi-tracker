"""Enums for the application."""

from enum import Enum


class WarningStatus(str, Enum):
    """Warning status values."""

    EMITIDO = "emitido"
    VIGENTE = "vigente"
    VENCIDO = "vencido"


class WarningSeverity(str, Enum):
    """Warning severity levels."""

    GREEN = "verde"
    YELLOW = "amarillo"
    ORANGE = "naranja"
    RED = "rojo"


SEVERITY_COLORS = {
    WarningSeverity.GREEN: "green",
    WarningSeverity.YELLOW: "#FFD700",
    WarningSeverity.ORANGE: "#FF8C00",
    WarningSeverity.RED: "red",
}

STATUS_COLORS = {
    WarningStatus.EMITIDO: "blue",
    WarningStatus.VIGENTE: "red",
    WarningStatus.VENCIDO: "white",
}
