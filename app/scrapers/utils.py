import re
from datetime import date, datetime


def parse_temperature(text: str) -> int:
    """Extract temperature value from text like '22ºC'."""
    match = re.search(r"(\d+)ºC", text)
    if match:
        return int(match.group(1))
    raise ValueError(f"Cannot parse temperature from: {text}")


def parse_date(date_text: str, year: int | None = None) -> date:
    """Parse Spanish date format to date object."""
    months_es = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    pattern = r"(\w+),\s+(\d+)\s+de\s+(\w+)"
    match = re.search(pattern, date_text.lower())

    if not match:
        raise ValueError(f"Cannot parse date from: {date_text}")

    day = int(match.group(2))
    month_name = match.group(3)

    month = months_es.get(month_name)
    if not month:
        raise ValueError(f"Unknown month: {month_name}")

    if year is None:
        year = datetime.now().year

    return date(year, month, day)


def parse_issued_date(issued_text: str) -> datetime:
    """
    Parse emission date from text like 'Emisión: martes, 11 de noviembre del 2025'.
    Returns datetime with time set to midnight.
    """
    months_es = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    pattern = r"(\w+),\s+(\d+)\s+de\s+(\w+)\s+del\s+(\d{4})"
    match = re.search(pattern, issued_text.lower())

    if not match:
        raise ValueError(f"Cannot parse issued date from: {issued_text}")

    day = int(match.group(2))
    month_name = match.group(3)
    year = int(match.group(4))

    month = months_es.get(month_name)
    if not month:
        raise ValueError(f"Unknown month: {month_name}")

    return datetime(year, month, day)
