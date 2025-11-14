"""
Utilitaires génériques pour la gestion et la recherche par dates.

Ce module fournit des fonctions réutilisables dans toute l'application
pour parser des dates en différents formats et filtrer des QuerySets Django.
"""

from datetime import datetime, date, timedelta
import re
from typing import Tuple

from django.db.models import QuerySet, Model


def try_parse_date(value: str) -> date:
    """Parse une chaîne de caractères en objet date.

    Supporte plusieurs formats courants :
    - YYYY-MM-DD (ISO)
    - DD/MM/YYYY
    - DD-MM-YYYY
    - YYYY/MM/DD
    - DDMMYYYY (8 chiffres sans séparateurs)
    - YYYYMMDD (8 chiffres sans séparateurs)

    Args:
        value: Chaîne représentant une date

    Returns:
        Un objet date Python

    Raises:
        ValueError: Si le format n'est pas reconnu
    """
    value = value.strip()

    # Formats avec séparateurs
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue

    # Formats sans séparateurs (8 chiffres)
    digits = re.sub(r"\D", "", value)
    if len(digits) == 8:
        # Essayer YYYYMMDD puis DDMMYYYY
        try:
            return datetime.strptime(digits, "%Y%m%d").date()
        except Exception:
            try:
                return datetime.strptime(digits, "%d%m%Y").date()
            except Exception:
                pass

    raise ValueError(f"Format de date non supporté: '{value}'")


def parse_date_input(date_input: str) -> Tuple[date, date]:
    """Parse une saisie utilisateur et retourne (date_début, date_fin).

    Supporte plusieurs formats :

    **Date unique :**
    - '2025-11-12' ou '12/11/2025' => start=end=date

    **Plages de dates :**
    - '2025-11-01 - 2025-11-10' (séparateur '-' ou 'to')

    **Mois complet :**
    - '2025-11' => plage du 1er au dernier jour du mois

    **Expressions naturelles (FR/EN) :**
    - "aujourd'hui" / "today"
    - "hier" / "yesterday"
    - "cette semaine" / "this week"
    - "7 derniers jours" / "7 days" / "7 last days"
    - "30 derniers jours" / "30 days" / "30 last days"
    - "ce mois" / "this month"
    - "le mois dernier" / "last month"

    Args:
        date_input: Chaîne représentant une date ou une plage

    Returns:
        Tuple (date_début, date_fin)

    Raises:
        ValueError: Si l'entrée est vide ou invalide
    """
    if not date_input or not str(date_input).strip():
        raise ValueError('date_input vide')

    raw = str(date_input).strip().lower()
    today = date.today()

    # Expressions naturelles courantes
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

    # Plages avec séparateur ' - ' ou ' to '
    if ' - ' in raw or ' to ' in raw:
        sep = ' - ' if ' - ' in raw else ' to '
        parts = [p.strip() for p in raw.split(sep, 1)]
        if len(parts) != 2:
            raise ValueError('Plage de dates invalide')
        start = try_parse_date(parts[0])
        end = try_parse_date(parts[1])
        if start > end:
            # Auto-correction : inverser si nécessaire
            start, end = end, start
        return start, end

    # Format mois uniquement : YYYY-MM
    m = re.match(r'^(\d{4})-(\d{2})$', raw)
    if m:
        y = int(m.group(1))
        mm = int(m.group(2))
        start = date(y, mm, 1)
        # Calculer le dernier jour du mois
        if mm == 12:
            end = date(y, 12, 31)
        else:
            end = date(y, mm + 1, 1) - timedelta(days=1)
        return start, end

    # Date unique
    d = try_parse_date(raw)
    return d, d


def search_by_date(
    model_class: type[Model],
    date_input: str,
    field: str = 'date_cmd'
) -> QuerySet:
    """Filtre un modèle Django par date de manière générique.

    Cette fonction peut être utilisée avec n'importe quel modèle Django
    possédant un champ date ou datetime.

    Args:
        model_class: La classe du modèle Django (ex: Commande, Livraison)
        date_input: Saisie utilisateur (voir parse_date_input pour les formats)
        field: Nom du champ du modèle à filtrer (défaut: 'date_cmd')

    Returns:
        QuerySet Django filtré (non-évalué)

    Examples:
        >>> from commande.models import Commande
        >>> qs = search_by_date(Commande, '2025-11-12')
        >>> qs = search_by_date(Commande, '2025-11-01 - 2025-11-10')
        >>> qs = search_by_date(Commande, 'cette semaine')
        >>> qs = search_by_date(Livraison, 'hier', field='date_livraison')

    Raises:
        ValueError: Si date_input est invalide
    """
    start_date, end_date = parse_date_input(date_input)

    # Tentative 1 : filtrage direct avec __range (fonctionne pour DateField et DateTimeField)
    try:
        qs = model_class.objects.filter(**{f"{field}__range": (start_date, end_date)})
        return qs
    except Exception:
        # Fallback : utiliser __date__range pour les DateTimeField nécessitant extraction
        qs = model_class.objects.filter(**{f"{field}__date__range": (start_date, end_date)})
        return qs
