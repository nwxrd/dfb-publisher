"""Periodo del respaldo (mismo naming que Issabel)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from calendar import monthrange

MONTHS = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE",
}


@dataclass(frozen=True)
class Period:
    year: int
    month: int

    @property
    def year_dir(self) -> str:
        return f"{self.year:04d}"

    @property
    def month_name(self) -> str:
        return MONTHS[self.month]

    @property
    def month_dir(self) -> str:
        return f"{self.month}-{self.month_name}"

    @property
    def label(self) -> str:
        return f"{self.month_name.capitalize()} {self.year}"

    def report_filename(self, prefix: str = "R_IT_AUD_002") -> str:
        return f"{prefix}_{self.month_name}_{self.year}.html"


def previous_month(today: date | None = None) -> Period:
    today = today or date.today()
    if today.month == 1:
        return Period(today.year - 1, 12)
    return Period(today.year, today.month - 1)


def parse_month(value: str) -> Period:
    """Parsea YYYY-MM."""
    parts = value.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"Mes inválido (use YYYY-MM): {value}")
    year = int(parts[0])
    month = int(parts[1])
    if year < 2000 or year > 2100 or month < 1 or month > 12:
        raise ValueError(f"Mes inválido (use YYYY-MM): {value}")
    monthrange(year, month)
    return Period(year, month)
