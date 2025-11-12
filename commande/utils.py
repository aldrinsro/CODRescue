from datetime import datetime, date
import re
from typing import Tuple

from django.db.models import QuerySet

from .models import Commande


def _try_parse_date(value: str) -> date:
    """Try several common date formats and return a date object.

    Supported formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD
    Raises ValueError if none match.
    """
    value = value.strip()
    # ISO YYYY-MM-DD or YYYY/MM/DD
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue

    # Try loose numeric patterns like DDMMYYYY or YYYYMMDD
    digits = re.sub(r"\D", "", value)
    if len(digits) == 8:
        # try YYYYMMDD then DDMMYYYY
        try:
            return datetime.strptime(digits, "%Y%m%d").date()
        except Exception:
            try:
                return datetime.strptime(digits, "%d%m%Y").date()
            except Exception:
                pass

    raise ValueError(f"Format de date non supporté: '{value}'")


def _parse_date_input(date_input: str) -> Tuple[date, date]:
    """Parse a user-provided date input and return (start_date, end_date).

    Accepts:
    - single date: '2025-11-12' or '12/11/2025' => start=end=date
    - range: '2025-11-01 - 2025-11-10' (separator '-' or 'to')
    - month: '2025-11' => full month range
    """
    if not date_input or not str(date_input).strip():
        raise ValueError('date_input vide')

    raw = str(date_input).strip().lower()

    # Expressions naturelles courantes
    from datetime import timedelta
    today = date.today()
    if raw in ["aujourd'hui", "today"]:
        return today, today
    if raw in ["hier", "yesterday"]:
        d = today - timedelta(days=1)
        return d, d
    if raw in ["cette semaine", "this week"]:
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, min(end, today)
    if raw in ["7 derniers jours", "7 days", "7 derniers jour", "7 last days"]:
        start = today - timedelta(days=6)
        return start, today
    if raw in ["30 derniers jours", "30 days", "30 derniers jour", "30 last days"]:
        start = today - timedelta(days=29)
        return start, today
    if raw in ["ce mois", "ce mois-ci", "this month"]:
        start = today.replace(day=1)
        return start, today
    if raw in ["le mois dernier", "mois dernier", "last month"]:
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start = last_month_end.replace(day=1)
        end = last_month_end
        return start, end

    # range using '-' or 'to'
    if ' - ' in raw or ' to ' in raw:
        sep = ' - ' if ' - ' in raw else ' to '
        parts = [p.strip() for p in raw.split(sep, 1)]
        if len(parts) != 2:
            raise ValueError('Plage de dates invalide')
        start = _try_parse_date(parts[0])
        end = _try_parse_date(parts[1])
        if start > end:
            # swap
            start, end = end, start
        return start, end

    # month-only format YYYY-MM
    m = re.match(r'^(\d{4})-(\d{2})$', raw)
    if m:
        y = int(m.group(1))
        mm = int(m.group(2))
        start = date(y, mm, 1)
        # compute last day of month simply
        if mm == 12:
            end = date(y, 12, 31)
        else:
            end = date(y, mm + 1, 1) - datetime.resolution
            end = end.date()
        return start, end

    # single date
    d = _try_parse_date(raw)
    return d, d


def search_commandes_by_date(date_input: str, field: str = 'date_cmd') -> QuerySet:
    """Return a QuerySet of Commande filtered by a date input.

    Parameters
    - date_input: string representing a single date, a range ("start - end") or a month (YYYY-MM)
    - field: model field name on `Commande` to filter by (default 'date_cmd')

    Examples
    - search_commandes_by_date('2025-11-12')
    - search_commandes_by_date('12/11/2025')
    - search_commandes_by_date('2025-11-01 - 2025-11-10')
    - search_commandes_by_date('2025-11')  # month

    Returns a Django QuerySet (not evaluated).
    """
    start_date, end_date = _parse_date_input(date_input)

    # Prefer direct range on DateField; use __date for DateTimeField if necessary.
    # Try field__range first (works for DateField and DateTimeField as well for full datetime),
    # but if the field is a DateTimeField and caller intends date-only filtering, use __date lookups.
    try:
        qs = Commande.objects.filter(**{f"{field}__range": (start_date, end_date)})
        return qs
    except Exception:
        # Fallback: try __date__range (for datetime fields needing date extractor)
        qs = Commande.objects.filter(**{f"{field}__date__range": (start_date, end_date)})
        return qs
