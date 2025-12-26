# -*- coding: utf-8 -*-
"""
Module de gestion des KPIs Ventes
Fonctions liees a analyse des ventes, CA, modeles et regions
REFACTORISE: Utilise maintenant les fonctions isolees du module calcul_ca
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from commande.models import Commande, Operation
from article.models import Article
from django.db.models import Q, Sum, Count, Avg, Max

# Import des fonctions de calcul CA isolees
from .utils.calcul_ca import (
    calcul_ca_avec_tendance,
    calcul_ca_journalier,
    calcul_ca_par_article,
    calcul_ca_par_region,
    calcul_ca_par_ville,
    calcul_panier_moyen,
    MethodeCalculCA
)

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
    
    # Si c'est déjà une chaîne, la retourner telle quelle
    return str(number)



@login_required
def ventes_data(request):
    """API pour les donnees de l'onglet Ventes - E-commerce telephonique Yoozak
    REFACTORISE: Utilise les fonctions isolees du module calcul_ca
    Support des périodes: 7j, 30j, 90j, mois (par défaut: mois en cours)
    """
    try:
        # ===== GESTION DE LA PÉRIODE =====
        periode = request.GET.get('period', 'mois')
        aujourd_hui = timezone.now().date()

        # Calculer les dates selon la période sélectionnée
        if periode == 'mois':
            # Mois en cours (comportement par défaut)
            debut_periode = aujourd_hui.replace(day=1)
            fin_periode = aujourd_hui
            # Période précédente = mois précédent
            debut_mois_precedent = (debut_periode - timedelta(days=1)).replace(day=1)
            fin_mois_precedent = debut_periode - timedelta(days=1)
            debut_periode_precedente = debut_mois_precedent
            fin_periode_precedente = fin_mois_precedent
        else:
            # Périodes en jours (7j, 30j, 90j)
            jours_map = {'7j': 7, '30j': 30, '90j': 90}
            nb_jours = jours_map.get(periode, 30)
            fin_periode = aujourd_hui
            debut_periode = aujourd_hui - timedelta(days=nb_jours)
            # Période précédente = même durée, avant
            fin_periode_precedente = debut_periode - timedelta(days=1)
            debut_periode_precedente = fin_periode_precedente - timedelta(days=nb_jours)

        # ===== KPI 1: CA AVEC TENDANCE =====
        ca_data = calcul_ca_avec_tendance(
            date_debut_actuel=debut_periode,
            date_fin_actuel=fin_periode,
            date_debut_precedent=debut_periode_precedente,
            date_fin_precedent=fin_periode_precedente,
            etats_inclus=['Livrée', 'Livrée Partiellement'],
            methode=MethodeCalculCA.METHODE_ACTIVE
        )

        # ===== KPI 2: PANIER MOYEN =====
        panier_moyen_actuel = calcul_panier_moyen(
            date_debut=debut_periode,
            date_fin=fin_periode,
            etats_inclus=['Livrée', 'Livrée Partiellement']
        )

        panier_moyen_precedent = calcul_panier_moyen(
            date_debut=debut_periode_precedente,
            date_fin=fin_periode_precedente,
            etats_inclus=['Livrée', 'Livrée Partiellement']
        )

        # Calcul tendance panier moyen
        if panier_moyen_precedent > 0:
            tendance_panier = ((panier_moyen_actuel - panier_moyen_precedent) / panier_moyen_precedent) * 100
        else:
            tendance_panier = 100 if panier_moyen_actuel > 0 else 0

        # ===== TOP 3 MODELES =====
        top_modeles_list = calcul_ca_par_article(
            date_debut=debut_periode,
            date_fin=fin_periode,
            limite=3,
            etats_inclus=['Livrée', 'Livrée Partiellement']
        )

        # ===== TOP 3 VILLES =====
        top_villes_list = calcul_ca_par_ville(
            date_debut=debut_periode,
            date_fin=fin_periode,
            limite=3,
            methode=MethodeCalculCA.METHODE_ACTIVE
        )

        # TOP 3 Commandes maximales (pour compatibilite)
        # IMPORTANT: Filtre par date de livraison (etats__date_debut)
        # Récupérer les 3 commandes avec les montants les plus élevés
        top_commandes = Commande.objects.filter(
            Q(etats__enum_etat__libelle__iexact='Livrée', etats__date_debut__gte=debut_periode, etats__date_debut__lte=fin_periode) |
            Q(etats__enum_etat__libelle__iexact='Livrée Partiellement', etats__date_debut__gte=debut_periode, etats__date_debut__lte=fin_periode)
        ).order_by('-total_cmd')[:3]

        # Construire la liste des TOP 3 commandes
        top_commandes_list = []
        if top_commandes:
            for commande in top_commandes:
                top_commandes_list.append({
                    'id_yz': commande.id_yz,
                    'montant': float(commande.total_cmd),
                    'montant_formate': format_number_fr(commande.total_cmd),
                    'date': commande.date_cmd.strftime('%d %b') if commande.date_cmd else 'N/A',
                    'client': f"{commande.client.prenom} {commande.client.nom[0]}." if commande.client and commande.client.nom else "Client",
                })

        # Pour compatibilité : garder aussi la commande max principale
        commande_max_montant = top_commandes_list[0]['montant'] if top_commandes_list else 0
        commande_max_numero = top_commandes_list[0]['id_yz'] if top_commandes_list else None
        commande_max_date = top_commandes_list[0]['date'] if top_commandes_list else None

        # ===== CONSTRUCTION DE LA REPONSE JSON =====
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'periode': periode,
            'methode_calcul': ca_data['methode_calcul'],

            'kpis_principaux': {
                'ca_periode': {
                    'valeur': ca_data['ca_actuel'],
                    'valeur_formatee': format_number_fr(ca_data['ca_actuel']),
                    'tendance': ca_data['tendance_pourcent'],
                    'unite': 'DH',
                    'label': 'CA Total',
                    'sub_value': f"Ce mois vs {format_number_fr(ca_data['ca_precedent'])} DH mois dernier"
                },
                'panier_moyen': {
                    'valeur': panier_moyen_actuel,
                    'valeur_formatee': format_number_fr(panier_moyen_actuel),
                    'tendance': round(tendance_panier, 1),
                    'unite': 'DH',
                    'label': 'Panier Moyen',
                    'sub_value': f"Ce mois vs {format_number_fr(panier_moyen_precedent)} DH mois dernier"
                },
                'nb_commandes': {
                    'valeur': ca_data['nb_commandes_actuel'],
                    'valeur_formatee': format_number_fr(ca_data['nb_commandes_actuel']),
                    'tendance': round(
                        ((ca_data['nb_commandes_actuel'] - ca_data['nb_commandes_precedent']) / ca_data['nb_commandes_precedent'] * 100)
                        if ca_data['nb_commandes_precedent'] > 0 else (100 if ca_data['nb_commandes_actuel'] > 0 else 0),
                        1
                    ),
                    'unite': 'commandes',
                    'label': 'Nb Commandes',
                    'sub_value': f"Ce mois vs {ca_data['nb_commandes_precedent']} mois dernier"
                }
            },

            'kpis_secondaires': {
                'top_modeles_kpi': [
                    {
                        'nom': modele['article_nom'],
                        'ca': modele['ca_total'],
                        'ca_formate': modele['ca_formate'],
                        'quantite': modele['quantite_vendue'],
                        'pourcentage': round((modele['ca_total'] / ca_data['ca_actuel'] * 100), 1) if ca_data['ca_actuel'] > 0 else 0,
                        'reference': modele['article_reference'],
                        'rang': idx + 1
                    } for idx, modele in enumerate(top_modeles_list)
                ] if top_modeles_list else [],
                'top_villes': [
                    {
                        'nom': ville['ville'],
                        'ca': ville['ca_total'],
                        'ca_formate': ville['ca_total_format'],
                        'pourcentage': ville['pourcentage'],
                        'rang': idx + 1
                    } for idx, ville in enumerate(top_villes_list)
                ] if top_villes_list else [],
                'commande_max': {
                    'valeur': commande_max_montant,
                    'valeur_formatee': format_number_fr(commande_max_montant),
                    'num_commande': commande_max_numero,
                    'date_commande': commande_max_date,
                    'sub_value': f"Nº{commande_max_numero} du {commande_max_date}" if commande_max_numero else "Aucune commande",
                    'tendance': 0,
                    'unite': 'DH'
                },
                'top_commandes_max': top_commandes_list,
                'top_modeles': [
                    {
                        'nom': modele['article_nom'],
                        'ca': modele['ca_total'],
                        'quantite': modele['quantite_vendue'],
                        'couleur': '#3b82f6',
                        'reference': modele['article_reference']
                    } for modele in top_modeles_list
                ]
            }
        }

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Erreur dans ventes_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des donnees Ventes'
        }, status=500)
    
    
@login_required
def evolution_ca_data(request):
    """API pour l'évolution du CA sur une période donnée
    REFACTORISE: Utilise calcul_ca_journalier() avec TOTAL_SANS_FRAIS
    """
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')
        jours_map = {'7j': 7, '30j': 30, '90j': 90}
        nb_jours = jours_map.get(periode, 30)

        # Dates avec timezone
        fin_date = timezone.now().date()
        debut_date = fin_date - timedelta(days=nb_jours)

        # Utiliser la fonction isolée de calcul CA journalier
        result = calcul_ca_journalier(
            date_debut=debut_date,
            date_fin=fin_date,
            etats_inclus=['Livrée', 'Livrée Partiellement'],
            methode=MethodeCalculCA.METHODE_ACTIVE
        )

        evolution_data = result['evolution']
        stats = result['statistiques']

        # Calcul de tendance : comparaison entre la première et la dernière semaine
        tendance = 0
        if len(evolution_data) >= 14:
            # Comparer première et dernière semaine
            premiere_semaine = evolution_data[:7]
            derniere_semaine = evolution_data[-7:]

            ca_debut = sum(d['ca'] for d in premiere_semaine) / 7
            ca_fin = sum(d['ca'] for d in derniere_semaine) / 7

            if ca_debut > 0:
                tendance = ((ca_fin - ca_debut) / ca_debut * 100)
        elif len(evolution_data) >= 7:
            # Si moins de 14 jours, comparer première et dernière moitié
            milieu = len(evolution_data) // 2
            premiere_moitie = evolution_data[:milieu]
            derniere_moitie = evolution_data[milieu:]

            ca_debut = sum(d['ca'] for d in premiere_moitie) / len(premiere_moitie) if premiere_moitie else 0
            ca_fin = sum(d['ca'] for d in derniere_moitie) / len(derniere_moitie) if derniere_moitie else 0

            if ca_debut > 0:
                tendance = ((ca_fin - ca_debut) / ca_debut * 100)

        response_data = {
            'success': True,
            'periode': periode,
            'methode_calcul': result['methode_calcul'],
            'evolution': evolution_data,
            'resume': {
                'ca_total': stats['ca_total'],
                'ca_moyen': stats['ca_moyen'],
                'ca_max_jour': stats['ca_max_jour'],
                'ca_min_jour': stats['ca_min_jour'],
                'tendance': round(tendance, 2),
                'nb_jours': nb_jours,
                'jours_avec_ventes': stats['jours_avec_ventes'],
                'taux_activite': stats['taux_activite']
            },
            'timestamp': timezone.now().isoformat()
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Erreur dans evolution_ca_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du calcul de l\'évolution du CA'
        }, status=500)

@login_required
def top_modeles_data(request):
    """API pour les données du top modèles par CA
    IMPORTANT: Filtre par la date de DEBUT de l'etat (date de livraison)
    """
    try:
        # Paramètres
        limite = int(request.GET.get('limit', 10))
        periode_jours = int(request.GET.get('days', 30))

        # Dates
        fin_date = timezone.now().date()
        debut_date = fin_date - timedelta(days=periode_jours)

        # Calcul des ventes par article/modèle basé sur les commandes livrées
        # IMPORTANT: Utilise etats__date_debut (date de livraison) au lieu de date_cmd
        top_modeles = Article.objects.annotate(
            ca_total=Sum(
                'paniers__sous_total',
                filter=Q(
                    paniers__commande__etats__date_debut__gte=debut_date,
                    paniers__commande__etats__date_debut__lte=fin_date,
                    paniers__commande__etats__date_fin__isnull=False
                ) & (
                    Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée') |
                    Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée Partiellement')
                )
            ),
            nb_ventes=Count(
                'paniers',
                filter=Q(
                    paniers__commande__etats__date_debut__gte=debut_date,
                    paniers__commande__etats__date_debut__lte=fin_date,
                    paniers__commande__etats__date_fin__isnull=False
                ) & (
                    Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée') |
                    Q(paniers__commande__etats__enum_etat__libelle__iexact='Livrée Partiellement')
                )
            )
        ).filter(
            ca_total__isnull=False,
            ca_total__gt=0
        ).order_by('-ca_total')[:limite]
          # Préparation des données (uniquement les données réelles)
        modeles_data = []
        couleurs = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#ec4899', '#6b7280', '#14b8a6', '#f97316', '#84cc16'
        ]
        
        for i, article in enumerate(top_modeles):
            modeles_data.append({
                'nom': article.nom,
                'reference': article.reference,
                'ca': float(article.ca_total or 0),
                'ca_formate': f"{article.ca_total or 0:,.0f} DH",
                'nb_ventes': article.nb_ventes or 0,
                'prix_moyen': float(article.ca_total / article.nb_ventes) if article.nb_ventes > 0 else 0,
                'couleur': couleurs[i % len(couleurs)]
            })
        
        # Statistiques
        ca_total = sum(m['ca'] for m in modeles_data)
        ca_moyen = ca_total / len(modeles_data) if modeles_data else 0
        
        response_data = {
            'success': True,
            'modeles': modeles_data,
            'stats': {
                'ca_total': ca_total,
                'ca_moyen': ca_moyen,
                'nb_modeles': len(modeles_data),
                'periode_jours': periode_jours
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement du top modèles'
        }, status=500)

@login_required
def performance_regions_data(request):
    """API pour les données de performance par région
    REFACTORISE: Utilise calcul_ca_par_region() avec TOTAL_SANS_FRAIS
    """
    try:
        # Période de référence (30 derniers jours par défaut)
        periode = request.GET.get('period', '30j')
        aujourd_hui = timezone.now().date()

        if periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=7)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=90)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=30)

        # Utiliser la fonction isolée de calcul CA par région
        regions_data = calcul_ca_par_region(
            date_debut=debut_periode,
            date_fin=aujourd_hui,
            limite=10,  # On récupère 10 régions
            etats_inclus=None,  # Par défaut: exclut les annulées
            methode=MethodeCalculCA.METHODE_ACTIVE
        )

        # Gérer le cas où il n'y a pas de données
        if not regions_data:
            return JsonResponse({
                'success': True,
                'regions': [],
                'stats': {
                    'total_regions': 0,
                    'ca_total_general': 0,
                    'ca_total_format': '0 DH',
                    'nb_commandes_total': 0,
                    'ca_moyen_general': 0
                },
                'periode': periode,
                'methode_calcul': MethodeCalculCA.METHODE_ACTIVE,
                'message': 'Aucune donnée disponible pour cette période',
                'empty': True
            })

        # Calculer le total général pour les statistiques
        total_ca_general = sum(region['ca_total'] for region in regions_data)
        nb_commandes_total = sum(region['nb_commandes'] for region in regions_data)

        # Couleurs pour différencier les régions
        couleurs = [
            '#3b82f6',  # Bleu
            '#10b981',  # Vert
            '#f59e0b',  # Orange
            '#ef4444',  # Rouge
            '#8b5cf6',  # Violet
            '#06b6d4',  # Cyan
            '#84cc16',  # Lime
            '#f97316',  # Orange foncé
        ]

        # Ajouter les couleurs aux régions
        for i, region in enumerate(regions_data):
            region['couleur'] = couleurs[i % len(couleurs)]
            # Renommer la clé 'region' en 'nom_region' pour compatibilité frontend
            region['nom_region'] = region['region']

        # Limiter aux 5 premières régions pour l'affichage
        top_regions = regions_data[:5]

        # Calculer les statistiques globales
        stats_globales = {
            'total_regions': len(regions_data),
            'ca_total_general': float(total_ca_general),
            'ca_total_format': f"{total_ca_general/1000000:.1f}M DH" if total_ca_general >= 1000000 else f"{total_ca_general/1000:.0f}K DH",
            'nb_commandes_total': nb_commandes_total,
            'ca_moyen_general': float(total_ca_general / len(regions_data)) if regions_data else 0
        }

        response_data = {
            'success': True,
            'regions': top_regions,
            'stats': stats_globales,
            'periode': periode,
            'methode_calcul': MethodeCalculCA.METHODE_ACTIVE,
            'message': f'Données chargées pour {len(top_regions)} régions'
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Erreur dans performance_regions_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des performances par région'
        }, status=500)

@login_required
def repartition_sources_data(request):
    """API pour la répartition des ventes par source de commande (Youcan, Shopify, etc.)
    Retourne les données pour un graphique Pie Chart
    """
    try:
        # Période de référence (30 derniers jours par défaut)
        periode = request.GET.get('period', '30j')
        aujourd_hui = timezone.now().date()

        if periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=7)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=90)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=30)

        # CORRECTION: Utiliser icontains au lieu de iexact pour gérer les problèmes d'accents
        # Debug: Compter le nombre total de commandes livrées
        total_commandes_livrees = Commande.objects.filter(
            etats__enum_etat__libelle__icontains='livr',
            etats__date_debut__gte=debut_periode,
            etats__date_debut__lte=aujourd_hui
        ).distinct().count()

        logger.info(f"📊 Répartition sources - Période: {periode} ({debut_periode} à {aujourd_hui})")
        logger.info(f"📦 Total commandes livrées: {total_commandes_livrees}")

        # Calculer la répartition par source
        repartition = Commande.objects.filter(
            etats__enum_etat__libelle__icontains='livr',
            etats__date_debut__gte=debut_periode,
            etats__date_debut__lte=aujourd_hui
        ).values('source').annotate(
            ca_total=Sum('total_cmd'),
            nb_commandes=Count('id')
        ).order_by('-ca_total')

        logger.info(f"🔍 Nombre de sources trouvées: {len(repartition)}")
        for item in repartition:
            logger.info(f"  - {item['source'] or 'NULL'}: {item['nb_commandes']} commandes, CA: {item['ca_total']}")

        # Couleurs spécifiques pour chaque source
        couleurs_sources = {
            'Youcan': '#3b82f6',      # Bleu
            'Shopify': '#10b981',     # Vert
            'Appel': '#f59e0b',       # Orange
            'Whatsapp ': '#25d366',   # Vert Whatsapp
            'Whatsapp': '#25d366',    # Vert Whatsapp (au cas où)
            'SMS': '#8b5cf6',         # Violet
            'Email': '#ef4444',       # Rouge
            'Facebook': '#1877f2',    # Bleu Facebook
        }

        sources_data = []
        ca_total_general = 0

        for item in repartition:
            source = item['source'] or 'Non défini'
            ca = float(item['ca_total'] or 0)
            ca_total_general += ca

            sources_data.append({
                'source': source,
                'ca': ca,
                'ca_formate': format_number_fr(ca),
                'nb_commandes': item['nb_commandes'],
                'couleur': couleurs_sources.get(source, '#6b7280')  # Gris par défaut
            })

        # Calculer les pourcentages
        for source in sources_data:
            source['pourcentage'] = round((source['ca'] / ca_total_general * 100), 1) if ca_total_general > 0 else 0

        response_data = {
            'success': True,
            'sources': sources_data,
            'stats': {
                'ca_total': ca_total_general,
                'ca_total_formate': format_number_fr(ca_total_general),
                'nb_sources': len(sources_data),
                'periode': periode
            },
            'timestamp': timezone.now().isoformat()
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Erreur dans repartition_sources_data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du calcul de la répartition par sources'
        }, status=500)
