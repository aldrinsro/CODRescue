# -*- coding: utf-8 -*-
"""
KPI Functions pour l'operateur logistique
Ce module contient les fonctions de calcul des indicateurs de performance (KPI)
"""

from django.db.models import Q, Count
from commande.models import Commande
import json


def get_distribution_repartition_stats():
    """
    Calcule la repartition des commandes qui ont ete mises en distribution et qui ne le sont plus.
    Exclut les commandes encore en etat "Mise en distribution".

    Returns:
        dict: Dictionnaire contenant les donnees formatees pour un graphique en camembert
            - labels: Liste des noms d'etats
            - data: Liste des nombres de commandes par etat
            - colors: Liste des couleurs associees a chaque etat
            - labels_json: Labels au format JSON pour JavaScript
            - data_json: Donnees au format JSON pour JavaScript
            - total: Nombre total de commandes ayant quitte l'etat "Mise en distribution"
    """

    # Recuperer les commandes qui ont ete mises en distribution ET qui ont quitte cet etat
    # (c'est-a-dire que l'etat "Mise en distribution" a une date_fin)
    commandes_distribution_terminees = Commande.objects.filter(
        etats__enum_etat__libelle="Mise en distribution",
        etats__date_fin__isnull=False  # L'etat "Mise en distribution" est termine
    ).values_list('id', flat=True).distinct()

    # Compter les commandes selon leur etat actuel (date_fin IS NULL)
    # Livree
    livrees = Commande.objects.filter(
        id__in=commandes_distribution_terminees,
        etats__enum_etat__libelle="Livrée",
        etats__date_fin__isnull=True
    ).distinct().count()

    # Livree Partiellement
    livrees_partiellement = Commande.objects.filter(
        id__in=commandes_distribution_terminees,
        etats__enum_etat__libelle="Livrée Partiellement",
        etats__date_fin__isnull=True
    ).distinct().count()

    # Retournee
    retournees = Commande.objects.filter(
        id__in=commandes_distribution_terminees,
        etats__enum_etat__libelle="Retournée",
        etats__date_fin__isnull=True
    ).distinct().count()

    # Reportee
    reportees = Commande.objects.filter(
        id__in=commandes_distribution_terminees,
        etats__enum_etat__libelle="Reportée",
        etats__date_fin__isnull=True
    ).distinct().count()

    # Total (commandes qui ont quitte l'etat "Mise en distribution")
    total = len(commandes_distribution_terminees)

    # Preparer les donnees pour le graphique
    labels = []
    data = []
    colors = []

    # Ajouter les donnees seulement si > 0
    if livrees > 0:
        labels.append('Livrée')
        data.append(livrees)
        colors.append('#10B981')  # Vert

    if livrees_partiellement > 0:
        labels.append('Livrée Partiellement')
        data.append(livrees_partiellement)
        colors.append('#3B82F6')  # Bleu

    if retournees > 0:
        labels.append('Retournée')
        data.append(retournees)
        colors.append('#EF4444')  # Rouge

    if reportees > 0:
        labels.append('Reportée')
        data.append(reportees)
        colors.append('#F59E0B')  # Orange

    # Convertir en JSON pour JavaScript
    labels_json = json.dumps(labels)
    data_json = json.dumps(data)
    colors_json = json.dumps(colors)

    return {
        'labels': labels,
        'data': data,
        'colors': colors,
        'labels_json': labels_json,
        'data_json': data_json,
        'colors_json': colors_json,
        'total': total,
        'livrees': livrees,
        'livrees_partiellement': livrees_partiellement,
        'retournees': retournees,
        'reportees': reportees
    }


def get_distribution_repartition_pourcentage():
    """
    Calcule les pourcentages de repartition des commandes mises en distribution.

    Returns:
        dict: Dictionnaire contenant les pourcentages de chaque etat
    """
    stats = get_distribution_repartition_stats()
    total = stats['total']

    if total == 0:
        return {
            'livrees_pct': 0,
            'livrees_partiellement_pct': 0,
            'retournees_pct': 0,
            'reportees_pct': 0
        }

    return {
        'livrees_pct': round((stats['livrees'] / total) * 100, 2),
        'livrees_partiellement_pct': round((stats['livrees_partiellement'] / total) * 100, 2),
        'retournees_pct': round((stats['retournees'] / total) * 100, 2),
        'reportees_pct': round((stats['reportees'] / total) * 100, 2)
    }
