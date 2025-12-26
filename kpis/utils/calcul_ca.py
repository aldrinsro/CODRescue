# -*- coding: utf-8 -*-
"""
Module de calcul du Chiffre d'Affaires (CA)
Contient toutes les fonctions de calcul isolees pour faciliter la maintenance
"""

from django.db.models import Sum, Count, Avg, Max, Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from commande.models import Commande
from article.models import Article

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION DES METHODES DE CALCUL
# =============================================================================

class MethodeCalculCA:
    """Configuration des differentes methodes de calcul du CA"""

    # Methode 1: CA base sur total_cmd (montant total de la commande)
    TOTAL_COMMANDE = 'total_commande'

    # Methode 2: CA base sur sum(sous_total) des paniers
    SUM_PANIERS = 'sum_paniers'

    # Methode 3: CA base sur total_cmd SANS les frais de livraison
    TOTAL_SANS_FRAIS = 'total_sans_frais'

    # Methode actuelle utilisee (modifiable facilement)
    METHODE_ACTIVE = TOTAL_SANS_FRAIS


# =============================================================================
# FONCTION 1: CALCUL DU CA POUR UNE PERIODE
# =============================================================================

def calcul_ca_periode(date_debut, date_fin, etats_inclus=None, methode=None):
    """
    Calcule le CA sur une periode donnee
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison), pas par date_cmd

    Args:
        date_debut (date): Date de debut de la periode
        date_fin (date): Date de fin de la periode
        etats_inclus (list): Liste des etats a inclure. Par defaut: ['Livree']
        methode (str): Methode de calcul (TOTAL_COMMANDE ou SUM_PANIERS)

    Returns:
        dict: {
            'ca_total': float,
            'nb_commandes': int,
            'methode_calcul': str,
            'periode': {'debut': str, 'fin': str}
        }

    Example:
        >>> result = calcul_ca_periode(
        ...     date_debut=date(2024, 12, 1),
        ...     date_fin=date(2024, 12, 31)
        ... )
        >>> print(result['ca_total'])
        150000.0
    """
    # Valeurs par defaut
    if etats_inclus is None:
        etats_inclus = ['Livrée', 'Livrée Partiellement']

    if methode is None:
        methode = MethodeCalculCA.METHODE_ACTIVE

    try:
        # Creer un filtre OR pour tous les etats avec leurs dates
        etat_filter = Q()
        for etat in etats_inclus:
            etat_filter |= Q(
                etats__enum_etat__libelle__iexact=etat,
                etats__date_debut__gte=date_debut,
                etats__date_debut__lte=date_fin
            )

        # Construction de la requete de base - filtre par date de debut de l'etat Livree
        queryset = Commande.objects.filter(etat_filter)

        # Calcul selon la methode choisie
        if methode == MethodeCalculCA.TOTAL_COMMANDE:
            # Methode 1: Somme des total_cmd
            ca_total = queryset.aggregate(total=Sum('total_cmd'))['total'] or 0

        elif methode == MethodeCalculCA.SUM_PANIERS:
            # Methode 2: Somme des sous_totaux des paniers
            ca_total = queryset.aggregate(
                total=Sum('paniers__sous_total')
            )['total'] or 0

        elif methode == MethodeCalculCA.TOTAL_SANS_FRAIS:
            # Methode 3: Somme des total_cmd SANS les frais de livraison
            from django.db.models import Case, When, F, Value, FloatField
            
            queryset_annote = queryset.annotate(
                frais=Case(
                    When(frais_livraison=True, ville__isnull=False, 
                         then=F('ville__frais_livraison')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                ca_sans_frais=F('total_cmd') - F('frais')
            )
            ca_total = queryset_annote.aggregate(total=Sum('ca_sans_frais'))['total'] or 0

        else:
            raise ValueError(f"Methode de calcul inconnue: {methode}")

        # Compter le nombre de commandes
        nb_commandes = queryset.distinct().count()

        return {
            'ca_total': float(ca_total),
            'nb_commandes': nb_commandes,
            'methode_calcul': methode,
            'periode': {
                'debut': date_debut.isoformat(),
                'fin': date_fin.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Erreur dans calcul_ca_periode: {str(e)}")
        return {
            'ca_total': 0.0,
            'nb_commandes': 0,
            'methode_calcul': methode,
            'periode': {
                'debut': date_debut.isoformat(),
                'fin': date_fin.isoformat()
            },
            'erreur': str(e)
        }


# =============================================================================
# FONCTION 2: CALCUL DU CA AVEC COMPARAISON (TENDANCE)
# =============================================================================

def calcul_ca_avec_tendance(date_debut_actuel, date_fin_actuel,
                           date_debut_precedent, date_fin_precedent,
                           etats_inclus=None, methode=None):
    """
    Calcule le CA avec comparaison entre deux periodes

    Args:
        date_debut_actuel (date): Debut periode actuelle
        date_fin_actuel (date): Fin periode actuelle
        date_debut_precedent (date): Debut periode precedente
        date_fin_precedent (date): Fin periode precedente
        etats_inclus (list): Etats a inclure
        methode (str): Methode de calcul

    Returns:
        dict: {
            'ca_actuel': float,
            'ca_precedent': float,
            'tendance_pourcent': float,
            'variation_absolue': float,
            'nb_commandes_actuel': int,
            'nb_commandes_precedent': int
        }
    """
    # Calcul periode actuelle
    result_actuel = calcul_ca_periode(
        date_debut_actuel, date_fin_actuel,
        etats_inclus=etats_inclus, methode=methode
    )

    # Calcul periode precedente
    result_precedent = calcul_ca_periode(
        date_debut_precedent, date_fin_precedent,
        etats_inclus=etats_inclus, methode=methode
    )

    ca_actuel = result_actuel['ca_total']
    ca_precedent = result_precedent['ca_total']

    # Calcul de la tendance
    if ca_precedent > 0:
        tendance = ((ca_actuel - ca_precedent) / ca_precedent) * 100
    else:
        tendance = 100.0 if ca_actuel > 0 else 0.0

    return {
        'ca_actuel': ca_actuel,
        'ca_precedent': ca_precedent,
        'tendance_pourcent': round(tendance, 1),
        'variation_absolue': ca_actuel - ca_precedent,
        'nb_commandes_actuel': result_actuel['nb_commandes'],
        'nb_commandes_precedent': result_precedent['nb_commandes'],
        'methode_calcul': result_actuel['methode_calcul']
    }


# =============================================================================
# FONCTION 3: CALCUL DU CA JOURNALIER (EVOLUTION)
# =============================================================================

def calcul_ca_journalier(date_debut, date_fin, etats_inclus=None, methode=None):
    """
    Calcule le CA jour par jour sur une periode
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison), pas par date_cmd

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin
        etats_inclus (list): Etats a inclure
        methode (str): Methode de calcul

    Returns:
        dict: {
            'evolution': [
                {'date': '2024-12-01', 'ca': 5000.0, ...},
                ...
            ],
            'statistiques': {
                'ca_total': float,
                'ca_moyen': float,
                'ca_max_jour': float,
                'ca_min_jour': float,
                'jours_avec_ventes': int,
                'taux_activite': float
            }
        }
    """
    if etats_inclus is None:
        etats_inclus = ['Livrée', 'Livrée Partiellement']

    if methode is None:
        methode = MethodeCalculCA.METHODE_ACTIVE

    try:
        # Creer un filtre OR pour tous les etats avec leurs dates
        etat_filter = Q()
        for etat in etats_inclus:
            etat_filter |= Q(
                etats__enum_etat__libelle__iexact=etat,
                etats__date_debut__gte=date_debut,
                etats__date_debut__lte=date_fin
            )

        # Construction requete de base - filtre par date de debut de l'etat Livree
        queryset = Commande.objects.filter(etat_filter)

        # Grouper par jour et calculer CA
        # IMPORTANT: On groupe par la date de debut de l'etat Livree
        if methode == MethodeCalculCA.TOTAL_COMMANDE:
            commandes_par_jour = queryset.extra(
                select={'date_seule': 'DATE(etats.date_debut)'},
                tables=['commande_etatcommande AS etats'],
                where=['commande_commande.id = etats.commande_id']
            ).values('date_seule').annotate(
                ca_jour=Sum('total_cmd')
            ).order_by('date_seule')

        elif methode == MethodeCalculCA.SUM_PANIERS:
            commandes_par_jour = queryset.extra(
                select={'date_seule': 'DATE(etats.date_debut)'},
                tables=['commande_etatcommande AS etats'],
                where=['commande_commande.id = etats.commande_id']
            ).values('date_seule').annotate(
                ca_jour=Sum('paniers__sous_total')
            ).order_by('date_seule')

        elif methode == MethodeCalculCA.TOTAL_SANS_FRAIS:
            from django.db.models import Case, When, F, Value, FloatField

            queryset_annote = queryset.annotate(
                frais=Case(
                    When(frais_livraison=True, ville__isnull=False,
                         then=F('ville__frais_livraison')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                ca_sans_frais=F('total_cmd') - F('frais')
            )
            commandes_par_jour = queryset_annote.extra(
                select={'date_seule': 'DATE(etats.date_debut)'},
                tables=['commande_etatcommande AS etats'],
                where=['commande_commande.id = etats.commande_id']
            ).values('date_seule').annotate(
                ca_jour=Sum('ca_sans_frais')
            ).order_by('date_seule')

        # Convertir en dictionnaire {date: ca}
        ca_par_jour = {}
        for cmd in commandes_par_jour:
            date_str = cmd['date_seule']
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_obj = date_str
            ca_par_jour[date_obj] = float(cmd['ca_jour'] or 0)

        # Remplir tous les jours (meme ceux sans ventes)
        evolution_data = []
        date_courante = date_debut if isinstance(date_debut, datetime.date) else date_debut.date()
        date_fin_obj = date_fin if isinstance(date_fin, datetime.date) else date_fin.date()

        while date_courante <= date_fin_obj:
            ca_jour = ca_par_jour.get(date_courante, 0)

            # Format de date plus lisible : "7 déc" au lieu de "07/12"
            mois_fr = ['janv', 'fév', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc']
            jour = date_courante.day
            mois = mois_fr[date_courante.month - 1]

            evolution_data.append({
                'date': date_courante.isoformat(),
                'date_formatee': f"{jour} {mois}",
                'ca': ca_jour,
                'ca_formate': f"{ca_jour:,.0f} DH" if ca_jour > 0 else "0 DH"
            })

            date_courante += timedelta(days=1)

        # Calculer statistiques
        ca_total = sum(d['ca'] for d in evolution_data)
        ca_moyen = ca_total / len(evolution_data) if evolution_data else 0
        jours_avec_ventes = len([d for d in evolution_data if d['ca'] > 0])
        ca_max_jour = max([d['ca'] for d in evolution_data]) if evolution_data else 0
        ca_min_jour = min([d['ca'] for d in evolution_data if d['ca'] > 0]) if jours_avec_ventes > 0 else 0

        nb_jours = len(evolution_data)
        taux_activite = (jours_avec_ventes / nb_jours * 100) if nb_jours > 0 else 0

        return {
            'evolution': evolution_data,
            'statistiques': {
                'ca_total': ca_total,
                'ca_moyen': ca_moyen,
                'ca_max_jour': ca_max_jour,
                'ca_min_jour': ca_min_jour,
                'jours_avec_ventes': jours_avec_ventes,
                'nb_jours_total': nb_jours,
                'taux_activite': round(taux_activite, 1)
            },
            'methode_calcul': methode
        }

    except Exception as e:
        logger.error(f"Erreur dans calcul_ca_journalier: {str(e)}")
        return {
            'evolution': [],
            'statistiques': {
                'ca_total': 0,
                'ca_moyen': 0,
                'ca_max_jour': 0,
                'ca_min_jour': 0,
                'jours_avec_ventes': 0,
                'nb_jours_total': 0,
                'taux_activite': 0
            },
            'methode_calcul': methode,
            'erreur': str(e)
        }


# =============================================================================
# FONCTION 4: CALCUL DU CA PAR ARTICLE
# =============================================================================

def calcul_ca_par_article(date_debut, date_fin, limite=10, etats_inclus=None):
    """
    Calcule le CA par article (toujours base sur les paniers)
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison), pas par date_cmd

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin
        limite (int): Nombre max d'articles a retourner
        etats_inclus (list): Etats a inclure

    Returns:
        list: [
            {
                'article_id': int,
                'article_nom': str,
                'ca_total': float,
                'quantite_vendue': int,
                'nb_commandes': int,
                'prix_moyen': float
            },
            ...
        ]
    """
    if etats_inclus is None:
        etats_inclus = ['Livrée', 'Livrée Partiellement']

    try:
        # Construction du filtre avec dates de l'etat Livree
        etat_filter = Q()
        for etat in etats_inclus:
            etat_filter |= Q(
                paniers__commande__etats__enum_etat__libelle__iexact=etat,
                paniers__commande__etats__date_debut__gte=date_debut,
                paniers__commande__etats__date_debut__lte=date_fin
            )

        # Requete
        articles = Article.objects.filter(etat_filter).annotate(
            ca_total=Sum('paniers__sous_total'),
            quantite_vendue=Sum('paniers__quantite'),
            nb_commandes=Count('paniers__commande', distinct=True)
        ).filter(
            ca_total__isnull=False,
            ca_total__gt=0
        ).order_by('-ca_total')[:limite]

        # Formater les resultats
        resultats = []
        for article in articles:
            prix_moyen = (
                float(article.ca_total / article.quantite_vendue)
                if article.quantite_vendue > 0
                else 0
            )

            resultats.append({
                'article_id': article.id,
                'article_nom': article.nom,
                'article_reference': getattr(article, 'reference', 'N/A'),
                'ca_total': float(article.ca_total or 0),
                'ca_formate': f"{article.ca_total or 0:,.0f} DH",
                'quantite_vendue': article.quantite_vendue or 0,
                'nb_commandes': article.nb_commandes or 0,
                'prix_moyen': prix_moyen
            })

        return resultats

    except Exception as e:
        logger.error(f"Erreur dans calcul_ca_par_article: {str(e)}")
        return []


# =============================================================================
# FONCTION 5: CALCUL DU CA PAR REGION
# =============================================================================

def calcul_ca_par_region(date_debut, date_fin, limite=10, etats_inclus=None, methode=None):
    """
    Calcule le CA par region geographique
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison), pas par date_cmd

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin
        limite (int): Nombre max de regions a retourner
        etats_inclus (list): Etats a inclure (default: exclut 'Annulee')
        methode (str): Methode de calcul

    Returns:
        list: [
            {
                'region': str,
                'ca_total': float,
                'nb_commandes': int,
                'ca_moyen': float,
                'pourcentage': float
            },
            ...
        ]
    """
    if etats_inclus is None:
        # Par defaut: prendre Livree et Livree Partiellement
        etats_inclus = ['Livrée', 'Livrée Partiellement']

    if methode is None:
        methode = MethodeCalculCA.METHODE_ACTIVE

    try:
        # Creer un filtre OR pour tous les etats avec leurs dates
        etat_filter = Q()
        for etat in etats_inclus:
            etat_filter |= Q(
                etats__enum_etat__libelle__iexact=etat,
                etats__date_debut__gte=date_debut,
                etats__date_debut__lte=date_fin
            )

        # Construction requete - filtre par date de debut de l'etat Livree
        queryset = Commande.objects.filter(
            etat_filter,
            ville__isnull=False,
            ville__region__isnull=False
        ).exclude(
            ville__region__nom_region__isnull=True
        ).exclude(
            ville__region__nom_region__exact=''
        )

        # Grouper par region
        if methode == MethodeCalculCA.TOTAL_COMMANDE:
            regions_data = queryset.values(
                'ville__region__nom_region'
            ).annotate(
                ca_total=Sum('total_cmd'),
                nb_commandes=Count('id'),
                ca_moyen=Avg('total_cmd')
            ).order_by('-ca_total')[:limite]

        elif methode == MethodeCalculCA.SUM_PANIERS:
            regions_data = queryset.values(
                'ville__region__nom_region'
            ).annotate(
                ca_total=Sum('paniers__sous_total'),
                nb_commandes=Count('id', distinct=True),
                ca_moyen=Avg('paniers__sous_total')
            ).order_by('-ca_total')[:limite]

        elif methode == MethodeCalculCA.TOTAL_SANS_FRAIS:
            from django.db.models import Case, When, F, Value, FloatField
            
            queryset_annote = queryset.annotate(
                frais=Case(
                    When(frais_livraison=True, ville__isnull=False, 
                         then=F('ville__frais_livraison')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                ca_sans_frais=F('total_cmd') - F('frais')
            )
            regions_data = queryset_annote.values(
                'ville__region__nom_region'
            ).annotate(
                ca_total=Sum('ca_sans_frais'),
                nb_commandes=Count('id'),
                ca_moyen=Avg('ca_sans_frais')
            ).order_by('-ca_total')[:limite]

        # Calculer le total general pour les pourcentages
        total_ca_general = sum(r['ca_total'] or 0 for r in regions_data)

        # Formater resultats
        resultats = []
        for region in regions_data:
            ca_total = region['ca_total'] or 0
            pourcentage = (ca_total / total_ca_general * 100) if total_ca_general > 0 else 0

            resultats.append({
                'region': region['ville__region__nom_region'],
                'ca_total': float(ca_total),
                'ca_total_format': f"{ca_total/1000:.0f}K DH" if ca_total >= 1000 else f"{ca_total:.0f} DH",
                'nb_commandes': region['nb_commandes'],
                'ca_moyen': float(region['ca_moyen'] or 0),
                'pourcentage': round(pourcentage, 1)
            })

        return resultats

    except Exception as e:
        logger.error(f"Erreur dans calcul_ca_par_region: {str(e)}")
        return []


# =============================================================================
# FONCTION 6: CALCUL DU CA PAR VILLE
# =============================================================================

def calcul_ca_par_ville(date_debut, date_fin, limite=10, etats_inclus=None, methode=None):
    """
    Calcule le CA par ville
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison), pas par date_cmd

    Args:
        date_debut (date): Date de debut
        date_fin (date): Date de fin
        limite (int): Nombre max de villes a retourner
        etats_inclus (list): Etats a inclure (default: Livree et Livree Partiellement)
        methode (str): Methode de calcul

    Returns:
        list: [
            {
                'ville': str,
                'ca_total': float,
                'nb_commandes': int,
                'ca_moyen': float,
                'pourcentage': float
            },
            ...
        ]
    """
    if etats_inclus is None:
        # Par defaut: prendre Livree et Livree Partiellement
        etats_inclus = ['Livrée', 'Livrée Partiellement']

    if methode is None:
        methode = MethodeCalculCA.METHODE_ACTIVE

    try:
        # Creer un filtre OR pour tous les etats avec leurs dates
        etat_filter = Q()
        for etat in etats_inclus:
            etat_filter |= Q(
                etats__enum_etat__libelle__iexact=etat,
                etats__date_debut__gte=date_debut,
                etats__date_debut__lte=date_fin
            )

        # Construction requete - filtre par date de debut de l'etat Livree
        queryset = Commande.objects.filter(
            etat_filter,
            ville__isnull=False
        ).exclude(
            ville__nom__isnull=True
        ).exclude(
            ville__nom__exact=''
        )

        # Grouper par ville
        if methode == MethodeCalculCA.TOTAL_COMMANDE:
            villes_data = queryset.values(
                'ville__nom'
            ).annotate(
                ca_total=Sum('total_cmd'),
                nb_commandes=Count('id'),
                ca_moyen=Avg('total_cmd')
            ).order_by('-ca_total')[:limite]

        elif methode == MethodeCalculCA.SUM_PANIERS:
            villes_data = queryset.values(
                'ville__nom'
            ).annotate(
                ca_total=Sum('paniers__sous_total'),
                nb_commandes=Count('id', distinct=True),
                ca_moyen=Avg('paniers__sous_total')
            ).order_by('-ca_total')[:limite]

        elif methode == MethodeCalculCA.TOTAL_SANS_FRAIS:
            from django.db.models import Case, When, F, Value, FloatField

            queryset_annote = queryset.annotate(
                frais=Case(
                    When(frais_livraison=True, ville__isnull=False,
                         then=F('ville__frais_livraison')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                ca_sans_frais=F('total_cmd') - F('frais')
            )
            villes_data = queryset_annote.values(
                'ville__nom'
            ).annotate(
                ca_total=Sum('ca_sans_frais'),
                nb_commandes=Count('id'),
                ca_moyen=Avg('ca_sans_frais')
            ).order_by('-ca_total')[:limite]

        # Calculer le total general pour les pourcentages
        total_ca_general = sum(v['ca_total'] or 0 for v in villes_data)

        # Formater resultats
        resultats = []
        for ville in villes_data:
            ca_total = ville['ca_total'] or 0
            pourcentage = (ca_total / total_ca_general * 100) if total_ca_general > 0 else 0

            resultats.append({
                'ville': ville['ville__nom'],
                'ca_total': float(ca_total),
                'ca_total_format': f"{ca_total/1000:.0f}K DH" if ca_total >= 1000 else f"{ca_total:.0f} DH",
                'nb_commandes': ville['nb_commandes'],
                'ca_moyen': float(ville['ca_moyen'] or 0),
                'pourcentage': round(pourcentage, 1)
            })

        return resultats

    except Exception as e:
        logger.error(f"Erreur dans calcul_ca_par_ville: {str(e)}")
        return []


# =============================================================================
# FONCTION HELPER: CALCUL PANIER MOYEN
# =============================================================================

def calcul_panier_moyen(date_debut, date_fin, etats_inclus=None):
    """
    Calcule le panier moyen sur une periode

    Returns:
        float: Montant moyen par commande
    """
    result = calcul_ca_periode(date_debut, date_fin, etats_inclus=etats_inclus)

    if result['nb_commandes'] > 0:
        return result['ca_total'] / result['nb_commandes']
    return 0.0
