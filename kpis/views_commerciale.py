# -*- coding: utf-8 -*-
"""
Module de gestion des KPIs Performance Commerciale
Fonctions liées à l'analyse des performances commerciales, sources, canaux
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from commande.models import Commande, Client
from article.models import Article
from django.db.models import Q, Sum, Count, F, Case, When, IntegerField
from django.db.models.functions import TruncDate

logger = logging.getLogger(__name__)


def format_number_fr(number, decimals=0):
    """Formate un nombre selon les standards français (espace comme séparateur de milliers)"""
    if number is None or (isinstance(number, (int, float)) and number == 0):
        return "0"

    if isinstance(number, (int, float)):
        if decimals == 0:
            # Pour les entiers, utiliser un format sans décimales
            return f"{number:,.0f}".replace(",", " ")
        else:
            # Pour les décimales
            return f"{number:,.{decimals}f}".replace(",", " ")

    return str(number)


@login_required
def commandes_par_source_data(request):
    """API pour récupérer les données des commandes par source (bar chart)

    TOUTES LES COMMANDES de la base de données (tous états confondus)
    Affiche uniquement le nombre de commandes par source (pas de CA)

    Retourne:
        - labels: Liste des sources
        - values: Nombre de commandes par source
        - stats: Statistiques globales
    """
    try:
        logger.info(f"📊 Commandes par source - TOUTES LES COMMANDES (tous états)")

        # Récupérer TOUTES les commandes avec leur source
        # IMPORTANT: Aucun filtre - toutes les commandes de la base
        commandes_par_source = Commande.objects.values('source').annotate(
            nb_commandes=Count('id')
        ).order_by('-nb_commandes')  # Trier par nombre de commandes décroissant

        logger.info(f"🔍 Nombre de sources trouvées: {len(commandes_par_source)}")

        # Construire les données pour le graphique
        labels = []
        values = []
        colors = []

        # Palette de couleurs pour les sources
        color_palette = [
            'rgba(59, 130, 246, 0.8)',   # Bleu
            'rgba(16, 185, 129, 0.8)',   # Vert
            'rgba(245, 158, 11, 0.8)',   # Orange
            'rgba(139, 92, 246, 0.8)',   # Violet
            'rgba(236, 72, 153, 0.8)',   # Rose
            'rgba(239, 68, 68, 0.8)',    # Rouge
            'rgba(14, 165, 233, 0.8)',   # Cyan
            'rgba(168, 85, 247, 0.8)',   # Pourpre
        ]

        for idx, item in enumerate(commandes_par_source):
            source_name = item['source'] or 'Non définie'
            nb_cmd = item['nb_commandes'] or 0

            labels.append(source_name)
            values.append(nb_cmd)
            colors.append(color_palette[idx % len(color_palette)])

            logger.info(f"  - {source_name}: {nb_cmd} commandes")

        # Calculer les statistiques
        total_commandes = sum(values)
        nb_sources = len(labels)

        if nb_sources > 0:
            source_principale = labels[0]
            nb_principale = values[0]
            percent_principale = (nb_principale / total_commandes * 100) if total_commandes > 0 else 0
        else:
            source_principale = "-"
            nb_principale = 0
            percent_principale = 0

        stats = {
            'total_commandes': total_commandes,
            'total_commandes_fmt': format_number_fr(total_commandes),
            'nb_sources': nb_sources,
            'source_principale': source_principale,
            'source_principale_nb': nb_principale,
            'source_principale_percent': round(percent_principale, 1),
            'source_principale_percent_fmt': f"{round(percent_principale, 1)}%"
        }

        logger.info(f"📈 Stats: {total_commandes} commandes, {nb_sources} sources, principale: {source_principale} ({percent_principale:.1f}%)")

        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values,
            'colors': colors,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans commandes_par_source_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def top_sources_trafic_data(request):
    """API pour récupérer le TOP 3 des sources de trafic (basé sur le champ source)

    Retourne le TOP 3 des sources avec:
        - nom: Nom de la source
        - nb_commandes: Nombre de commandes
        - ca_total: CA généré
        - badge_color: Couleur du badge (or, argent, bronze)
    """
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')

        # Calcul des dates
        aujourd_hui = timezone.now().date()

        if periode == 'mois':
            debut_periode = aujourd_hui.replace(day=1)
        elif periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=6)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=89)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=29)

        logger.info(f"🏆 Top sources trafic - Période: {periode} ({debut_periode} à {aujourd_hui})")

        # Récupérer le TOP 3 des sources par nombre de commandes
        top_sources = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='livr'),
            etats__date_debut__date__gte=debut_periode,
            etats__date_debut__date__lte=aujourd_hui
        ).values('source').annotate(
            nb_commandes=Count('id', distinct=True),
            ca_total=Sum('total_cmd')
        ).order_by('-nb_commandes')[:3]

        # Couleurs des badges pour le podium
        badge_colors = ['yellow', 'gray', 'orange']  # Or, Argent, Bronze

        top_sources_list = []
        for idx, source in enumerate(top_sources):
            source_name = source['source'] or 'Non définie'
            nb_cmd = source['nb_commandes'] or 0
            ca = source['ca_total'] or 0

            top_sources_list.append({
                'nom': source_name,
                'nb_commandes': nb_cmd,
                'nb_commandes_fmt': format_number_fr(nb_cmd),
                'ca_total': float(ca),
                'ca_total_fmt': format_number_fr(ca, 2),
                'badge_color': badge_colors[idx],
                'rank': idx + 1
            })

            logger.info(f"  #{idx + 1} - {source_name}: {nb_cmd} commandes, CA: {ca:.2f} DH")

        return JsonResponse({
            'success': True,
            'top_sources': top_sources_list
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans top_sources_trafic_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def top_canaux_data(request):
    """API pour récupérer le TOP 3 des canaux de vente (basé sur le champ origine)

    Retourne le TOP 3 des canaux avec:
        - nom: Nom du canal
        - nb_commandes: Nombre de commandes
        - ca_total: CA généré
    """
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')

        # Calcul des dates
        aujourd_hui = timezone.now().date()

        if periode == 'mois':
            debut_periode = aujourd_hui.replace(day=1)
        elif periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=6)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=89)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=29)

        logger.info(f"🏪 Top canaux - Période: {periode} ({debut_periode} à {aujourd_hui})")

        # Récupérer le TOP 3 des canaux par CA
        top_canaux = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='livr'),
            etats__date_debut__date__gte=debut_periode,
            etats__date_debut__date__lte=aujourd_hui
        ).values('origine').annotate(
            nb_commandes=Count('id', distinct=True),
            ca_total=Sum('total_cmd')
        ).order_by('-ca_total')[:3]

        badge_colors = ['yellow', 'gray', 'orange']

        top_canaux_list = []
        for idx, canal in enumerate(top_canaux):
            canal_name = canal['origine'] or 'Non défini'
            nb_cmd = canal['nb_commandes'] or 0
            ca = canal['ca_total'] or 0

            top_canaux_list.append({
                'nom': canal_name,
                'nb_commandes': nb_cmd,
                'nb_commandes_fmt': format_number_fr(nb_cmd),
                'ca_total': float(ca),
                'ca_total_fmt': format_number_fr(ca, 2),
                'badge_color': badge_colors[idx],
                'rank': idx + 1
            })

            logger.info(f"  #{idx + 1} - {canal_name}: {nb_cmd} commandes, CA: {ca:.2f} DH")

        return JsonResponse({
            'success': True,
            'top_canaux': top_canaux_list
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans top_canaux_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def evolution_conversion_data(request):
    """API pour l'évolution du taux de conversion sur une période

    Retourne:
        - labels: Dates
        - values: Taux de conversion par jour (%)
        - stats: Statistiques (moyenne, max, tendance)
    """
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')

        # Calcul des dates
        aujourd_hui = timezone.now().date()

        if periode == 'mois':
            debut_periode = aujourd_hui.replace(day=1)
        elif periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=6)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=89)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=29)

        logger.info(f"📈 Evolution conversion - Période: {periode} ({debut_periode} à {aujourd_hui})")

        # Pour le taux de conversion, nous devons calculer:
        # Taux = (Commandes livrées / Total commandes) * 100

        # Récupérer toutes les commandes par jour (groupées par date de création)
        commandes_totales_par_jour = Commande.objects.filter(
            date_cmd__gte=debut_periode,
            date_cmd__lte=aujourd_hui
        ).annotate(
            date=TruncDate('date_cmd')
        ).values('date').annotate(
            total=Count('id')
        ).order_by('date')

        # Récupérer les commandes livrées par jour
        commandes_livrees_par_jour = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='livr'),
            etats__date_debut__date__gte=debut_periode,
            etats__date_debut__date__lte=aujourd_hui
        ).annotate(
            date=TruncDate('etats__date_debut')
        ).values('date').annotate(
            livrees=Count('id', distinct=True)
        ).order_by('date')

        # Créer un dictionnaire pour faciliter le lookup
        livrees_dict = {item['date']: item['livrees'] for item in commandes_livrees_par_jour}

        labels = []
        values = []

        for item in commandes_totales_par_jour:
            date = item['date']
            total = item['total'] or 0
            livrees = livrees_dict.get(date, 0)

            # Calculer le taux de conversion
            taux = (livrees / total * 100) if total > 0 else 0

            labels.append(date.strftime('%d/%m'))
            values.append(round(taux, 2))

        # Calculer les statistiques
        if len(values) > 0:
            conversion_moyenne = round(sum(values) / len(values), 2)
            conversion_max = round(max(values), 2)

            # Tendance: comparer première moitié vs deuxième moitié
            mid = len(values) // 2
            if mid > 0:
                premiere_moitie = sum(values[:mid]) / mid
                deuxieme_moitie = sum(values[mid:]) / (len(values) - mid)
                tendance = "hausse" if deuxieme_moitie > premiere_moitie else "baisse"
                tendance_value = round(((deuxieme_moitie - premiere_moitie) / premiere_moitie * 100) if premiere_moitie > 0 else 0, 1)
            else:
                tendance = "stable"
                tendance_value = 0
        else:
            conversion_moyenne = 0
            conversion_max = 0
            tendance = "stable"
            tendance_value = 0

        stats = {
            'conversion_moyenne': conversion_moyenne,
            'conversion_moyenne_fmt': f"{conversion_moyenne}%",
            'conversion_max': conversion_max,
            'conversion_max_fmt': f"{conversion_max}%",
            'tendance': tendance,
            'tendance_value': tendance_value,
            'tendance_fmt': f"{tendance_value:+.1f}%"
        }

        logger.info(f"📊 Stats conversion: Moyenne: {conversion_moyenne}%, Max: {conversion_max}%, Tendance: {tendance} ({tendance_value:+.1f}%)")

        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans evolution_conversion_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def segmentation_clients_data(request):
    """API pour la répartition des clients par segment (Nouveaux, Réguliers, VIP)

    Segments:
        - Nouveaux: 1 commande
        - Réguliers: 2-4 commandes
        - VIP: 5+ commandes

    Retourne:
        - labels: Segments
        - values: Nombre de clients par segment
        - colors: Couleurs pour le pie chart
    """
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')

        # Calcul des dates
        aujourd_hui = timezone.now().date()

        if periode == 'mois':
            debut_periode = aujourd_hui.replace(day=1)
        elif periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=6)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=89)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=29)

        logger.info(f"🎯 Segmentation clients - Période: {periode} ({debut_periode} à {aujourd_hui})")

        # Compter le nombre de commandes par client sur la période
        clients_avec_commandes = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='livr'),
            etats__date_debut__date__gte=debut_periode,
            etats__date_debut__date__lte=aujourd_hui
        ).values('client').annotate(
            nb_commandes=Count('id', distinct=True)
        )

        # Segmenter les clients
        nouveaux = 0
        reguliers = 0
        vip = 0

        for item in clients_avec_commandes:
            nb_cmd = item['nb_commandes']
            if nb_cmd == 1:
                nouveaux += 1
            elif 2 <= nb_cmd <= 4:
                reguliers += 1
            else:  # 5+
                vip += 1

        labels = ['Nouveaux', 'Réguliers', 'VIP']
        values = [nouveaux, reguliers, vip]
        colors = [
            'rgba(59, 130, 246, 0.8)',   # Bleu pour nouveaux
            'rgba(16, 185, 129, 0.8)',   # Vert pour réguliers
            'rgba(245, 158, 11, 0.8)'    # Orange pour VIP
        ]

        logger.info(f"📊 Segmentation: Nouveaux: {nouveaux}, Réguliers: {reguliers}, VIP: {vip}")

        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values,
            'colors': colors,
            'total_clients': nouveaux + reguliers + vip
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans segmentation_clients_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def taux_doublons_data(request):
    """API pour calculer le taux de doublons dans toutes les commandes

    Un doublon est une commande ayant l'état "Doublon" dans EnumEtatCmd

    SANS FILTRE DE PÉRIODE - Analyse toute la base de données

    Retourne:
        - total_commandes: Nombre total de commandes
        - nb_doublons: Nombre de commandes marquées comme doublon
        - taux_doublons: Taux de doublons (%)
    """
    try:
        logger.info(f"🔍 Calcul du taux de doublons - TOUTE LA BASE")

        # Récupérer TOUTES les commandes
        total_commandes = Commande.objects.count()

        # Compter les commandes avec l'état "Doublon"
        # Utiliser icontains pour gérer les variations possibles (Doublon, doublon, etc.)
        nb_commandes_doublons = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='doublon')
        ).distinct().count()

        # Calculer le taux de doublons
        taux_doublons = (nb_commandes_doublons / total_commandes * 100) if total_commandes > 0 else 0

        logger.info(f"📊 Doublons: {nb_commandes_doublons}/{total_commandes} commandes ({taux_doublons:.2f}%)")

        return JsonResponse({
            'success': True,
            'total_commandes': total_commandes,
            'total_commandes_fmt': format_number_fr(total_commandes),
            'nb_doublons': nb_commandes_doublons,
            'nb_doublons_fmt': format_number_fr(nb_commandes_doublons),
            'nb_groupes': 0,  # Pas de notion de groupes ici
            'nb_groupes_fmt': '-',
            'taux_doublons': round(taux_doublons, 2),
            'taux_doublons_fmt': f"{round(taux_doublons, 2)}%"
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans taux_doublons_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def taux_erronees_data(request):
    """API pour calculer le taux de commandes erronées dans toutes les commandes

    Une commande erronée est une commande ayant l'état "Erronée" dans EnumEtatCmd

    SANS FILTRE DE PÉRIODE - Analyse toute la base de données

    Retourne:
        - total_commandes: Nombre total de commandes
        - nb_erronees: Nombre de commandes marquées comme erronées
        - taux_erronees: Taux de commandes erronées (%)
    """
    try:
        logger.info(f"🔍 Calcul du taux de commandes erronées - TOUTE LA BASE")

        # Récupérer TOUTES les commandes
        total_commandes = Commande.objects.count()

        # Compter les commandes avec l'état "Erronée"
        # Utiliser icontains pour gérer les variations possibles (Erronée, erronee, erronnee, etc.)
        nb_commandes_erronees = Commande.objects.filter(
            Q(etats__enum_etat__libelle__icontains='erron')
        ).distinct().count()

        # Calculer le taux de commandes erronées
        taux_erronees = (nb_commandes_erronees / total_commandes * 100) if total_commandes > 0 else 0

        logger.info(f"📊 Erronées: {nb_commandes_erronees}/{total_commandes} commandes ({taux_erronees:.2f}%)")

        return JsonResponse({
            'success': True,
            'total_commandes': total_commandes,
            'total_commandes_fmt': format_number_fr(total_commandes),
            'nb_erronees': nb_commandes_erronees,
            'nb_erronees_fmt': format_number_fr(nb_commandes_erronees),
            'taux_erronees': round(taux_erronees, 2),
            'taux_erronees_fmt': f"{round(taux_erronees, 2)}%"
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans taux_erronees_data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
