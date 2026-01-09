"""
Utilitaires génériques pour le filtrage dans toute l'application.

Ce module fournit des fonctions réutilisables pour appliquer des filtres
standards (date, synchronisation, tri) à n'importe quel modèle Django.
"""

from datetime import datetime, timedelta
from django.db.models import QuerySet
from django.utils import timezone
from .date_utils import parse_date_input


def apply_date_filter(queryset: QuerySet, request, field: str = 'date_creation') -> QuerySet:
    """Applique un filtre de date à un QuerySet.

    Args:
        queryset: QuerySet Django à filtrer
        request: Objet HttpRequest contenant les paramètres GET
        field: Nom du champ de date à filtrer (défaut: 'date_creation')

    Returns:
        QuerySet filtré par date

    Examples:
        >>> queryset = apply_date_filter(Commande.objects.all(), request)
        >>> queryset = apply_date_filter(Client.objects.all(), request, field='date_inscription')
    """
    date_filter = request.GET.get('date_filter', '')
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')

    # Intervalle personnalisé prioritaire
    if date_start or date_end:
        try:
            if date_start and date_end:
                start_date = datetime.strptime(date_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_end, '%Y-%m-%d').date()
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            elif date_start:
                start_date = datetime.strptime(date_start, '%Y-%m-%d').date()
                end_date = timezone.now().date()
            else:
                start_date = datetime(2000, 1, 1).date()
                end_date = datetime.strptime(date_end, '%Y-%m-%d').date()

            queryset = queryset.filter(**{
                f'{field}__date__gte': start_date,
                f'{field}__date__lte': end_date
            })
        except ValueError:
            pass
    elif date_filter:
        # Filtre prédéfini (aujourd'hui, cette semaine, etc.)
        try:
            start_date, end_date = parse_date_input(date_filter)
            queryset = queryset.filter(**{
                f'{field}__date__gte': start_date,
                f'{field}__date__lte': end_date
            })
        except ValueError:
            pass

    return queryset


def apply_sync_filter(queryset: QuerySet, request,
                     sync_date_field: str = 'last_sync_date',
                     origin_field: str = 'origine') -> QuerySet:
    """Applique un filtre de synchronisation à un QuerySet.

    Args:
        queryset: QuerySet Django à filtrer
        request: Objet HttpRequest contenant les paramètres GET
        sync_date_field: Nom du champ de date de synchronisation
        origin_field: Nom du champ indiquant l'origine (pour filtrer 'SYNC')

    Returns:
        QuerySet filtré par synchronisation

    Examples:
        >>> queryset = apply_sync_filter(Commande.objects.all(), request)
        >>> queryset = apply_sync_filter(Article.objects.all(), request, 'date_sync', 'type')
    """
    sync_filter = request.GET.get('sync_filter', '')
    sync_date_start = request.GET.get('sync_date_start', '')
    sync_date_end = request.GET.get('sync_date_end', '')

    if not sync_filter:
        return queryset

    # Filtrer uniquement les éléments synchronisés
    queryset = queryset.filter(**{origin_field: 'SYNC'})

    # Intervalle personnalisé prioritaire
    if sync_date_start or sync_date_end:
        try:
            if sync_date_start and sync_date_end:
                start_date = datetime.strptime(sync_date_start, '%Y-%m-%d')
                end_date = datetime.strptime(sync_date_end, '%Y-%m-%d')
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
                # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
                end_date = end_date.replace(hour=23, minute=59, second=59)
            elif sync_date_start:
                start_date = datetime.strptime(sync_date_start, '%Y-%m-%d')
                end_date = timezone.now()
            else:
                start_date = datetime(2000, 1, 1)
                end_date = datetime.strptime(sync_date_end, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)

            queryset = queryset.filter(**{
                f'{sync_date_field}__gte': start_date,
                f'{sync_date_field}__lte': end_date
            })
        except ValueError:
            pass
    elif sync_filter == 'last_minute':
        queryset = queryset.filter(**{
            f'{sync_date_field}__gte': timezone.now() - timedelta(minutes=1)
        })
    elif sync_filter == 'last_hour':
        queryset = queryset.filter(**{
            f'{sync_date_field}__gte': timezone.now() - timedelta(hours=1)
        })
    elif sync_filter == 'today':
        queryset = queryset.filter(**{
            f'{sync_date_field}__date': timezone.now().date()
        })
    elif sync_filter == 'last_24_hours':
        queryset = queryset.filter(**{
            f'{sync_date_field}__gte': timezone.now() - timedelta(hours=24)
        })
    elif sync_filter == 'last_7_days':
        queryset = queryset.filter(**{
            f'{sync_date_field}__gte': timezone.now() - timedelta(days=7)
        })

    return queryset


def apply_date_cmd_filter(queryset: QuerySet, request, field: str = 'date_cmd') -> QuerySet:
    """Applique un filtre de date de commande à un QuerySet.

    Args:
        queryset: QuerySet Django à filtrer
        request: Objet HttpRequest contenant les paramètres GET
        field: Nom du champ de date de commande à filtrer (défaut: 'date_cmd')

    Returns:
        QuerySet filtré par date de commande

    Examples:
        >>> queryset = apply_date_cmd_filter(Commande.objects.all(), request)
    """
    date_cmd_filter = request.GET.get('date_cmd_filter', '')
    date_cmd_start = request.GET.get('date_cmd_start', '')
    date_cmd_end = request.GET.get('date_cmd_end', '')

    # Intervalle personnalisé prioritaire
    if date_cmd_start or date_cmd_end:
        try:
            if date_cmd_start and date_cmd_end:
                start_date = datetime.strptime(date_cmd_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_cmd_end, '%Y-%m-%d').date()
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            elif date_cmd_start:
                start_date = datetime.strptime(date_cmd_start, '%Y-%m-%d').date()
                end_date = timezone.now().date()
            else:
                start_date = datetime(2000, 1, 1).date()
                end_date = datetime.strptime(date_cmd_end, '%Y-%m-%d').date()

            queryset = queryset.filter(**{
                f'{field}__gte': start_date,
                f'{field}__lte': end_date
            })
        except ValueError:
            pass
    elif date_cmd_filter:
        # Filtre prédéfini (aujourd'hui, cette semaine, etc.)
        try:
            start_date, end_date = parse_date_input(date_cmd_filter)
            queryset = queryset.filter(**{
                f'{field}__gte': start_date,
                f'{field}__lte': end_date
            })
        except ValueError:
            pass

    return queryset


def apply_order_filter(queryset: QuerySet, request,
                      allowed_fields: list = None) -> QuerySet:
    """Applique un tri à un QuerySet.

    Args:
        queryset: QuerySet Django à trier
        request: Objet HttpRequest contenant les paramètres GET
        allowed_fields: Liste des champs autorisés pour le tri
                       Si None, utilise une liste par défaut

    Returns:
        QuerySet trié

    Examples:
        >>> queryset = apply_order_filter(Commande.objects.all(), request)
        >>> custom_fields = ['name', '-name', 'date', '-date']
        >>> queryset = apply_order_filter(Client.objects.all(), request, custom_fields)
    """
    order_by = request.GET.get('order_by', '')

    if not order_by:
        return queryset

    # Liste par défaut des champs autorisés
    if allowed_fields is None:
        allowed_fields = [
            'date_creation', '-date_creation',
            'date_cmd', '-date_cmd',
            'total_cmd', '-total_cmd',
            'client__nom', '-client__nom',
            'id_yz', '-id_yz'
        ]

    if order_by in allowed_fields:
        queryset = queryset.order_by(order_by)

    return queryset


def apply_all_filters(queryset: QuerySet, request,
                     date_field: str = 'date_creation',
                     date_cmd_field: str = 'date_cmd',
                     sync_date_field: str = 'last_sync_date',
                     origin_field: str = 'origine',
                     allowed_order_fields: list = None) -> QuerySet:
    """Applique tous les filtres standards (date, date_cmd, sync, order) à un QuerySet.

    Cette fonction combine les 4 filtres en un seul appel pour plus de simplicité.

    Args:
        queryset: QuerySet Django à filtrer
        request: Objet HttpRequest contenant les paramètres GET
        date_field: Nom du champ de date pour le filtre de date de création
        date_cmd_field: Nom du champ de date pour le filtre de date de commande
        sync_date_field: Nom du champ de date de synchronisation
        origin_field: Nom du champ indiquant l'origine
        allowed_order_fields: Liste des champs autorisés pour le tri

    Returns:
        QuerySet filtré et trié

    Examples:
        >>> from common.filter_utils import apply_all_filters
        >>> commandes = Commande.objects.all()
        >>> commandes = apply_all_filters(commandes, request)
    """
    queryset = apply_date_filter(queryset, request, date_field)
    queryset = apply_date_cmd_filter(queryset, request, date_cmd_field)
    queryset = apply_sync_filter(queryset, request, sync_date_field, origin_field)
    queryset = apply_order_filter(queryset, request, allowed_order_fields)
    return queryset


def get_filter_context(request) -> dict:
    """Retourne un dictionnaire avec les valeurs des filtres pour le contexte du template.

    Args:
        request: Objet HttpRequest Django

    Returns:
        dict: Dictionnaire contenant les valeurs des filtres

    Examples:
        >>> context.update(get_filter_context(request))
    """
    return {
        'date_filter': str(request.GET.get('date_filter', '')),
        'date_cmd_filter': str(request.GET.get('date_cmd_filter', '')),
        'sync_filter': str(request.GET.get('sync_filter', '')),
        'order_by': str(request.GET.get('order_by', '')),
    }


def apply_commande_filters(queryset: QuerySet, request) -> QuerySet:
    """Applique les filtres de commandes avancés à un QuerySet.

    Cette fonction gère tous les filtres du composant commande-filters.html :
    - Recherche globale (N° commande, client, téléphone, email)
    - Filtres spécifiques (ville, région, adresse, dates, montant, état, opérateur)

    Args:
        queryset: QuerySet de Commande à filtrer
        request: Objet HttpRequest contenant les paramètres GET

    Returns:
        QuerySet filtré

    Examples:
        >>> from common.filter_utils import apply_commande_filters
        >>> commandes = Commande.objects.all()
        >>> commandes = apply_commande_filters(commandes, request)
    """
    from django.db.models import Q

    # Recherche globale (smartSearch)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__tel__icontains=search_query) |
            Q(client__email__icontains=search_query)
        )

    # Filtre par N° Commande (id_yz)
    filter_id_yz = request.GET.get('filter_id_yz', '').strip()
    if filter_id_yz:
        queryset = queryset.filter(id_yz__icontains=filter_id_yz)

    # Filtre par N° Externe (num_cmd)
    filter_num_cmd = request.GET.get('filter_num_cmd', '').strip()
    if filter_num_cmd:
        queryset = queryset.filter(num_cmd__icontains=filter_num_cmd)

    # Filtre par Client
    filter_client = request.GET.get('filter_client', '').strip()
    if filter_client:
        queryset = queryset.filter(
            Q(client__nom__icontains=filter_client) |
            Q(client__prenom__icontains=filter_client)
        )

    # Filtre par Téléphone
    filter_phone = request.GET.get('filter_phone', '').strip()
    if filter_phone:
        queryset = queryset.filter(client__tel__icontains=filter_phone)

    # Filtre par Email
    filter_email = request.GET.get('filter_email', '').strip()
    if filter_email:
        queryset = queryset.filter(client__email__icontains=filter_email)

    # Filtre par Ville Client
    filter_ville_client = request.GET.get('filter_ville_client', '').strip()
    if filter_ville_client:
        queryset = queryset.filter(ville__nom__icontains=filter_ville_client)

    # Filtre par Ville & Région
    filter_ville_region = request.GET.get('filter_ville_region', '').strip()
    if filter_ville_region:
        queryset = queryset.filter(
            Q(ville__nom__icontains=filter_ville_region) |
            Q(ville__region__nom__icontains=filter_ville_region)
        )

    # Filtre par Adresse
    filter_adresse = request.GET.get('filter_adresse', '').strip()
    if filter_adresse:
        queryset = queryset.filter(client__adresse__icontains=filter_adresse)

    # Filtres par Date
    filter_date_commande = request.GET.get('filter_date_commande', '').strip()
    if filter_date_commande:
        try:
            date = datetime.strptime(filter_date_commande, '%Y-%m-%d').date()
            queryset = queryset.filter(date_cmd=date)
        except ValueError:
            pass

    filter_date_confirmation = request.GET.get('filter_date_confirmation', '').strip()
    if filter_date_confirmation:
        try:
            date = datetime.strptime(filter_date_confirmation, '%Y-%m-%d').date()
            queryset = queryset.filter(
                etats__enum_etat__libelle='Confirmée',
                etats__date_debut__date=date
            ).distinct()
        except ValueError:
            pass

    filter_date_affectation = request.GET.get('filter_date_affectation', '').strip()
    if filter_date_affectation:
        try:
            date = datetime.strptime(filter_date_affectation, '%Y-%m-%d').date()
            queryset = queryset.filter(
                etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                etats__date_debut__date=date
            ).distinct()
        except ValueError:
            pass

    filter_date_preparation = request.GET.get('filter_date_preparation', '').strip()
    if filter_date_preparation:
        try:
            date = datetime.strptime(filter_date_preparation, '%Y-%m-%d').date()
            queryset = queryset.filter(
                etats__enum_etat__libelle='En préparation',
                etats__date_debut__date=date
            ).distinct()
        except ValueError:
            pass

    filter_date_livraison = request.GET.get('filter_date_livraison', '').strip()
    if filter_date_livraison:
        try:
            date = datetime.strptime(filter_date_livraison, '%Y-%m-%d').date()
            queryset = queryset.filter(
                etats__enum_etat__libelle='En livraison',
                etats__date_debut__date=date
            ).distinct()
        except ValueError:
            pass

    # Filtres par Montant
    filter_total_min = request.GET.get('filter_total_min', '').strip()
    if filter_total_min:
        try:
            total_min = float(filter_total_min)
            queryset = queryset.filter(total_cmd__gte=total_min)
        except ValueError:
            pass

    filter_total_max = request.GET.get('filter_total_max', '').strip()
    if filter_total_max:
        try:
            total_max = float(filter_total_max)
            queryset = queryset.filter(total_cmd__lte=total_max)
        except ValueError:
            pass

    # Filtre par État
    filter_etat = request.GET.get('filter_etat', '').strip()
    if filter_etat:
        queryset = queryset.filter(
            etats__enum_etat__libelle__icontains=filter_etat,
            etats__date_fin__isnull=True
        ).distinct()

    # Filtre par Opérateur
    filter_operateur = request.GET.get('filter_operateur', '').strip()
    if filter_operateur:
        queryset = queryset.filter(
            Q(etats__operateur__nom__icontains=filter_operateur) |
            Q(etats__operateur__prenom__icontains=filter_operateur),
            etats__date_fin__isnull=True
        ).distinct()

    return queryset
