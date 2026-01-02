"""
================================================================================
MODULE GLOBAL: Utilitaires de Gestion du Compteur Upsell
================================================================================

Ce module fournit des fonctions réutilisables pour la gestion du système upsell
dans les commandes.

Fonctionnalités:
- Détermination automatique du type de prix gelé
- Mise à jour dynamique des types de prix selon le compteur
- Recalcul automatique du compteur upsell
- Recalcul des remises après changement de compteur

Règles métier du système upsell:
- Compteur 0 (0-1 article upsell) → Prix normal
- Compteur 1 (2 articles upsell) → Prix upsell 2
- Compteur 2 (3 articles upsell) → Prix upsell 3
- Compteur 3 (4 articles upsell) → Prix upsell 4
- Compteur 4+ (5+ articles upsell) → Prix gros

@version 1.0
@author YZ-RESCUE
"""


def determiner_type_prix_gele(article, compteur):
    """
    Détermine le type de prix gelé à enregistrer dans le panier.

    Le type de prix est déterminé selon une hiérarchie de priorités:

    PRIORITÉ 1: Les phases spéciales (promotion, liquidation, test) sont TOUJOURS gelées,
                même pour les articles upsell.

    PRIORITÉ 2: Les articles upsell en phase normale → enregistrer le niveau upsell actuel
                basé sur le compteur au moment de la création du panier.

    PRIORITÉ 3: Les articles normaux en phase normale ont le type 'normal'.

    Args:
        article: Instance d'Article
        compteur (int): Compteur upsell actuel de la commande

    Returns:
        str: Type de prix gelé ('promotion', 'liquidation', 'test',
             'upsell_niveau_1/2/3/4', ou 'normal')

    Example:
        >>> article = Article.objects.get(id=1)
        >>> type_prix = determiner_type_prix_gele(article, compteur=2)
        >>> print(type_prix)  # 'upsell_niveau_2' si article upsell en phase normale
    """
    # PRIORITÉ 1: Phases spéciales et promotions (même pour les articles upsell)
    # Ces types doivent être gelés car ils représentent des prix spéciaux
    if hasattr(article, 'has_promo_active') and article.has_promo_active:
        return 'promotion'
    elif article.phase == 'LIQUIDATION':
        return 'liquidation'
    elif article.phase == 'EN_TEST':
        return 'test'

    # PRIORITÉ 2: Articles upsell en phase normale → enregistrer le niveau selon le compteur
    # Le niveau upsell est gelé au moment de l'ajout du panier
    if article.isUpsell:
        if compteur == 0:
            return 'normal'  # Pas encore de niveau upsell
        elif compteur == 1:
            return 'upsell_niveau_1'
        elif compteur == 2:
            return 'upsell_niveau_2'
        elif compteur == 3:
            return 'upsell_niveau_3'
        elif compteur >= 4:
            return 'upsell_niveau_4'
        else:
            return 'normal'

    # PRIORITÉ 3: Articles normaux en phase normale
    return 'normal'


def mettre_a_jour_types_prix_gele_upsell(commande):
    """
    Met à jour dynamiquement les type_prix_gele de tous les paniers upsell
    en fonction du compteur actuel de la commande.

    Cette fonction doit être appelée après chaque modification du panier qui peut
    impacter le compteur (ajout, suppression, modification de quantité).

    ⚠️ IMPORTANT: Seuls les paniers upsell en phase normale sont mis à jour.
    Les paniers en promotion, liquidation ou test conservent leur type_prix_gele fixe.

    Args:
        commande: Instance de Commande

    Returns:
        None

    Side effects:
        - Met à jour le champ `type_prix_gele` des paniers upsell
        - Affiche des logs de debug

    Example:
        >>> commande = Commande.objects.get(id=123)
        >>> mettre_a_jour_types_prix_gele_upsell(commande)
        🔄 Panier 45 mis à jour: upsell_niveau_1 → upsell_niveau_2 (compteur=2)
    """
    from commande.models import Panier

    # Récupérer tous les paniers upsell de la commande
    paniers_upsell = commande.paniers.filter(article__isUpsell=True)

    for panier in paniers_upsell:
        article = panier.article

        # Recalculer le type_prix_gele basé sur le compteur actuel
        nouveau_type = determiner_type_prix_gele(article, commande.compteur)

        # Mettre à jour uniquement si le type a changé et que ce n'est pas une phase spéciale
        # (les phases spéciales restent figées)
        if nouveau_type != panier.type_prix_gele and nouveau_type not in ['promotion', 'liquidation', 'test']:
            ancien_type = panier.type_prix_gele
            panier.type_prix_gele = nouveau_type
            panier.save(update_fields=['type_prix_gele'])
            print(f"🔄 Panier {panier.id} mis à jour: {ancien_type} → {nouveau_type} (compteur={commande.compteur})")


def recalculer_remises_apres_changement_compteur(commande):
    """
    Recalcule toutes les remises personnalisées des paniers après un changement de compteur upsell.

    Cette fonction est nécessaire car:
    - Le compteur upsell détermine le prix unitaire effectif
    - Les remises en pourcentage dépendent du prix effectif
    - Quand le compteur change, toutes les remises doivent être recalculées

    Process:
    1. Récupère tous les paniers avec remise personnalisée
    2. Recalcule le prix effectif selon le nouveau compteur
    3. Recalcule le montant de la remise
    4. Met à jour les sous-totaux

    Args:
        commande: Instance de Commande

    Returns:
        None

    Side effects:
        - Met à jour les champs des RemisePersonnalisee
        - Met à jour les sous-totaux des Panier
        - Affiche des logs de debug

    Example:
        >>> commande = Commande.objects.get(id=123)
        >>> recalculer_remises_apres_changement_compteur(commande)
        🏷️ Remise recalculée pour panier 45: 200.00 DH - 20.00 DH = 180.00 DH
    """
    from decimal import Decimal
    from commande.templatetags.remise_filters import calculer_prix_unitaire_effectif

    # Récupérer tous les paniers avec une remise personnalisée
    paniers_avec_remise = commande.paniers.filter(remise_appliquer=True).prefetch_related('remise_personnalisee')

    for panier in paniers_avec_remise:
        if hasattr(panier, 'remise_personnalisee'):
            remise = panier.remise_personnalisee

            # Recalculer le sous-total basé sur le prix effectif actuel (avec le nouveau compteur)
            prix_unitaire_effectif = calculer_prix_unitaire_effectif(panier)
            quantite = Decimal(str(panier.quantite))
            sous_total_sans_remise = prix_unitaire_effectif * quantite

            # Mettre à jour le sous_total_remise
            panier.sous_total_remise = float(sous_total_sans_remise)

            # Recalculer le montant de la remise
            montant_remise = remise.calculer_montant_remise()
            remise.montant_applique = float(montant_remise)
            remise.save()

            # Recalculer le sous-total avec remise
            sous_total_avec_remise = sous_total_sans_remise - montant_remise
            panier.sous_total = float(sous_total_avec_remise)
            panier.save()

            print(f"   🏷️ Remise recalculée pour panier {panier.id}: {sous_total_sans_remise} DH - {montant_remise} DH = {sous_total_avec_remise} DH")


def recalculer_compteur_upsell(commande):
    """
    Recalcule le compteur upsell de la commande et met à jour tous les paniers concernés.

    Cette fonction centralise toute la logique de recalcul du compteur upsell:
    1. Compte les articles upsell dans la commande
    2. Applique la règle métier: compteur = max(0, total_upsell - 1) si total >= 2, sinon 0
    3. Met à jour les type_prix_gele de tous les paniers upsell
    4. Recalcule tous les totaux de la commande
    5. Recalcule toutes les remises personnalisées si le compteur a changé

    Règle métier:
    - 0-1 articles upsell → compteur = 0 (prix normal)
    - 2+ articles upsell → compteur = total - 1

    Args:
        commande: Instance de Commande à recalculer

    Returns:
        None

    Side effects:
        - Met à jour commande.compteur
        - Appelle mettre_a_jour_types_prix_gele_upsell()
        - Appelle commande.recalculer_totaux_upsell()
        - Appelle recalculer_remises_apres_changement_compteur() si nécessaire
        - Affiche des logs de debug

    Example:
        >>> commande = Commande.objects.get(id=123)
        >>> recalculer_compteur_upsell(commande)
        🔄 Compteur upsell changé: 1 → 2
        🔄 Compteur upsell recalculé: 2 (total articles upsell: 3)
    """
    from django.db.models import Sum

    # Compter la quantité totale d'articles upsell
    total_quantite_upsell = commande.paniers.filter(
        article__isUpsell=True
    ).aggregate(total=Sum('quantite'))['total'] or 0

    # Règle métier: Le compteur s'incrémente à partir de 2 unités d'articles upsell
    # 0-1 unités → compteur = 0
    # 2+ unités → compteur = total - 1
    ancien_compteur = commande.compteur
    if total_quantite_upsell >= 2:
        commande.compteur = total_quantite_upsell - 1
    else:
        commande.compteur = 0

    commande.save()

    # Mettre à jour les type_prix_gele de tous les paniers upsell
    mettre_a_jour_types_prix_gele_upsell(commande)

    # Recalculer tous les totaux
    commande.recalculer_totaux_upsell()

    # Si le compteur a changé, recalculer toutes les remises personnalisées
    if ancien_compteur != commande.compteur:
        print(f"🔄 Compteur upsell changé: {ancien_compteur} → {commande.compteur}")
        recalculer_remises_apres_changement_compteur(commande)

    print(f"🔄 Compteur upsell recalculé: {commande.compteur} (total articles upsell: {total_quantite_upsell})")


__all__ = [
    'determiner_type_prix_gele',
    'mettre_a_jour_types_prix_gele_upsell',
    'recalculer_remises_apres_changement_compteur',
    'recalculer_compteur_upsell',
]
