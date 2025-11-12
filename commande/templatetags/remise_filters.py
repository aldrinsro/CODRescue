from django import template
from decimal import Decimal, ROUND_HALF_UP

register = template.Library()


def calculer_prix_unitaire_effectif(panier):
    """
    Calcule le prix unitaire effectif d'un panier en tenant compte de:
    - Promotion active (priorité 1)
    - Phase LIQUIDATION (priorité 2)
    - Phase EN_TEST (priorité 3)
    - Upsell avec compteur (priorité 4)
    - Prix normal (défaut)

    Cette fonction est utilisée pour calculer les remises en pourcentage
    sur le prix actuel réel (et non sur prix_panier gelé).

    Args:
        panier: L'objet Panier

    Returns:
        Decimal: Prix unitaire effectif
    """
    article = panier.article
    commande = panier.commande

    # Promotion active - priorité sur tout
    if hasattr(article, 'has_promo_active') and article.has_promo_active:
        return Decimal(str(article.prix_actuel or article.prix_unitaire))

    # Phase liquidation
    if article.phase == 'LIQUIDATION':
        prix_liq = article.Prix_liquidation if hasattr(article, 'Prix_liquidation') and article.Prix_liquidation else article.prix_actuel or article.prix_unitaire
        return Decimal(str(prix_liq))

    # Phase test
    if article.phase == 'EN_TEST':
        return Decimal(str(article.prix_actuel or article.prix_unitaire))

    # Article upsell avec compteur
    if hasattr(article, 'isUpsell') and article.isUpsell and commande.compteur > 0:
        if commande.compteur == 1 and article.prix_upsell_1:
            return Decimal(str(article.prix_upsell_1))
        elif commande.compteur == 2 and article.prix_upsell_2:
            return Decimal(str(article.prix_upsell_2))
        elif commande.compteur == 3 and article.prix_upsell_3:
            return Decimal(str(article.prix_upsell_3))
        elif commande.compteur >= 4 and article.prix_upsell_4:
            return Decimal(str(article.prix_upsell_4))

    # Prix normal
    return Decimal(str(article.prix_actuel or article.prix_unitaire))

@register.filter
def get_prix_affichage_remise(article, quantite=1):
    """
    Détermine le prix d'affichage selon la phase de l'article et les remises disponibles.
    Remplace les conditions complexes dans les templates.

    IMPORTANT: Cette fonction ne doit PAS appliquer automatiquement les prix de remise.
    Les prix de remise ne sont appliqués que si remise_appliquer = True dans le panier.
    Utilisez get_prix_effectif_panier pour les paniers avec remises appliquées.

    Args:
        article: L'objet Article
        quantite: La quantité (défaut 1)

    Returns:
        dict: {
            'prix': prix à afficher,
            'libelle': libellé du prix,
            'couleur_classe': classe CSS pour la couleur,
            'icone': icône FontAwesome,
            'type': type de prix appliqué
        }
    """
    if not article:
        return {
            'prix': 0,
            'libelle': 'Article non trouvé',
            'couleur_classe': 'text-gray-500',
            'icone': 'fas fa-question',
            'type': 'error'
        }

    # Promotion active - priorité maximale
    if hasattr(article, 'has_promo_active') and article.has_promo_active:
        prix = article.prix_actuel or article.prix_unitaire
        return {
            'prix': prix,
            'libelle': 'Prix promotion',
            'couleur_classe': 'text-red-600',
            'icone': 'fas fa-fire',
            'type': 'promotion'
        }

    # Phase liquidation - utilise Prix_liquidation si disponible
    if article.phase == 'LIQUIDATION':
        prix = article.Prix_liquidation if hasattr(article, 'Prix_liquidation') and article.Prix_liquidation else article.prix_actuel or article.prix_unitaire
        return {
            'prix': prix,
            'libelle': 'Prix liquidation',
            'couleur_classe': 'text-orange-600',
            'icone': 'fas fa-tags',
            'type': 'liquidation'
        }

    # Phase test
    if article.phase == 'EN_TEST':
        prix = article.prix_actuel or article.prix_unitaire
        return {
            'prix': prix,
            'libelle': 'Prix test',
            'couleur_classe': 'text-blue-600',
            'icone': 'fas fa-flask',
            'type': 'test'
        }

    # Article upsell - gestion des prix par quantité
    if hasattr(article, 'isUpsell') and article.isUpsell:
        if quantite <= 1:
            prix = article.prix_actuel or article.prix_unitaire
            libelle = 'Prix normal'
        elif quantite >= 2 and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1:
            prix = article.prix_upsell_1
            libelle = 'Prix upsell niveau 1'
        elif quantite >= 3 and hasattr(article, 'prix_upsell_2') and article.prix_upsell_2:
            prix = article.prix_upsell_2
            libelle = 'Prix upsell niveau 2'
        elif quantite >= 4 and hasattr(article, 'prix_upsell_3') and article.prix_upsell_3:
            prix = article.prix_upsell_3
            libelle = 'Prix upsell niveau 3'
        elif quantite >= 5 and hasattr(article, 'prix_upsell_4') and article.prix_upsell_4:
            prix = article.prix_upsell_4
            libelle = 'Prix Gros'
        else:
            prix = article.prix_actuel or article.prix_unitaire
            libelle = 'Prix normal'

        return {
            'prix': prix,
            'libelle': libelle,
            'couleur_classe': 'text-green-600',
            'icone': 'fas fa-arrow-up',
            'type': 'upsell'
        }

    # Prix normal par défaut
    prix = article.prix_actuel or article.prix_unitaire
    return {
        'prix': prix,
        'libelle': 'Prix normal',
        'couleur_classe': 'text-gray-600',
        'icone': 'fas fa-tag',
        'type': 'normal'
    }

@register.filter
def get_prix_remise_applicable(article, niveau_remise):
    """
    Retourne le prix de remise selon le niveau spécifié.
    
    Args:
        article: L'objet Article
        niveau_remise: Le niveau de remise (1, 2, 3, 4 ou 'liquidation')
        
    Returns:
        Decimal: Prix de remise ou None si non disponible
    """
    if not article:
        return None
        
    if niveau_remise == 1:
        return getattr(article, 'prix_remise_1', None)
    elif niveau_remise == 2:
        return getattr(article, 'prix_remise_2', None)
    elif niveau_remise == 3:
        return getattr(article, 'prix_remise_3', None)
    elif niveau_remise == 4:
        return getattr(article, 'prix_remise_4', None)
    
    return None

@register.filter
def calcul_economie_remise(article, prix_remise):
    """
    Calcule l'économie réalisée avec une remise.
    
    Args:
        article: L'objet Article
        prix_remise: Prix de la remise
        
    Returns:
        dict: {
            'economie': montant économisé,
            'pourcentage': pourcentage d'économie
        }
    """
    if not article or not prix_remise:
        return {'economie': 0, 'pourcentage': 0}
    
    prix_normal = article.prix_actuel or article.prix_unitaire
    if not prix_normal or prix_remise >= prix_normal:
        return {'economie': 0, 'pourcentage': 0}
    
    economie = Decimal(str(prix_normal)) - Decimal(str(prix_remise))
    pourcentage = (economie / Decimal(str(prix_normal)) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return {
        'economie': economie,
        'pourcentage': pourcentage
    }

@register.filter
def format_prix_avec_devise(prix, devise='DH'):
    """
    Formate un prix avec la devise.
    Args:
        prix: Le prix à formater
        devise: La devise (défaut 'DH')  
    Returns:
        str: Prix formaté avec devise
    """
    if prix is None:
        return f"0,00 {devise}"
    
    try:
        # Convertir en Decimal pour un formatage précis
        prix_decimal = Decimal(str(prix))
        # Formater avec 2 décimales et virgule comme séparateur
        prix_formate = f"{prix_decimal:.2f}".replace('.', ',')
        return f"{prix_formate} {devise}"
    except (ValueError, TypeError, AttributeError):
        return f"0,00 {devise}"

@register.filter
def get_prix_effectif_panier(panier):
    """
    Retourne le prix effectif d'un panier en prenant en compte les remises déjà appliquées.
    Utilise le champ remise_appliquer et type_remise_appliquee pour déterminer le prix.
    
    Args:
        panier: L'objet Panier
        
    Returns:
        dict: {
            'prix_unitaire': prix unitaire effectif,
            'sous_total': sous-total effectif,
            'libelle': libellé du prix,
            'couleur_classe': classe CSS,
            'icone': icône FontAwesome,
            'est_remise': True si une remise est détectée
        }
    """
    if not panier or not panier.article or panier.quantite <= 0:
        return {
            'prix_unitaire': 0,
            'sous_total': 0,
            'libelle': 'Erreur panier',
            'couleur_classe': 'text-gray-500',
            'icone': 'fas fa-question',
            'est_remise': False
        }
    
    article = panier.article
    quantite = panier.quantite
    sous_total_actuel = Decimal(str(panier.sous_total))
    prix_unitaire_effectif = sous_total_actuel / Decimal(str(quantite))

    # PRIORITÉ 1: Utiliser le type de prix gelé si disponible
    # EXCEPTION: Les types upsell_niveau_X ne sont PAS utilisés pour l'affichage
    # car le libellé upsell doit être dynamique selon le compteur actuel
    if hasattr(panier, 'type_prix_gele') and panier.type_prix_gele:
        type_prix_gele = panier.type_prix_gele

        # IGNORER les types upsell_niveau_X → ils seront recalculés dynamiquement
        if not type_prix_gele.startswith('upsell_niveau_'):
            # Mapper le type de prix gelé vers un libellé et style
            if type_prix_gele == 'liquidation':
                return {
                    'prix_unitaire': float(prix_unitaire_effectif),
                    'sous_total': float(sous_total_actuel),
                    'libelle': 'Prix liquidation',
                    'couleur_classe': 'text-orange-600',
                    'icone': 'fas fa-tags',
                    'est_remise': False
                }
            elif type_prix_gele == 'promotion':
                return {
                    'prix_unitaire': float(prix_unitaire_effectif),
                    'sous_total': float(sous_total_actuel),
                    'libelle': 'Prix promotion',
                    'couleur_classe': 'text-red-600',
                    'icone': 'fas fa-fire',
                    'est_remise': False
                }
            elif type_prix_gele == 'test':
                return {
                    'prix_unitaire': float(prix_unitaire_effectif),
                    'sous_total': float(sous_total_actuel),
                    'libelle': 'Prix test',
                    'couleur_classe': 'text-blue-600',
                    'icone': 'fas fa-flask',
                    'est_remise': False
                }
            elif type_prix_gele == 'normal':
                return {
                    'prix_unitaire': float(prix_unitaire_effectif),
                    'sous_total': float(sous_total_actuel),
                    'libelle': 'Prix normal',
                    'couleur_classe': 'text-gray-600',
                    'icone': 'fas fa-tag',
                    'est_remise': False
                }

    # Logique standard pour déterminer le prix
    # Calculer dynamiquement le libellé selon le compteur actuel
    from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur

    # Obtenir le prix selon le compteur actuel de la commande
    commande = panier.commande
    compteur_actuel = commande.compteur
    prix_avec_compteur = get_prix_upsell_avec_compteur(article, compteur_actuel)

    # Déterminer le libellé selon la PRIORITÉ :
    # 1. Phases spéciales (promotion, liquidation, test) ont TOUJOURS la priorité
    # 2. Upsell uniquement si pas de phase spéciale
    # 3. Normal par défaut

    if hasattr(article, 'has_promo_active') and article.has_promo_active:
        # PRIORITÉ 1: Promotion active
        libelle = 'Prix promotion'
        couleur_classe = 'text-red-600'
        icone = 'fas fa-fire'
    elif article.phase == 'LIQUIDATION':
        # PRIORITÉ 1: Phase liquidation
        libelle = 'Prix liquidation'
        couleur_classe = 'text-orange-600'
        icone = 'fas fa-tags'
    elif article.phase == 'EN_TEST':
        # PRIORITÉ 1: Phase test
        libelle = 'Prix test'
        couleur_classe = 'text-blue-600'
        icone = 'fas fa-flask'
    elif compteur_actuel > 0 and hasattr(article, 'isUpsell') and article.isUpsell:
        # PRIORITÉ 2: Upsell dynamique (seulement si pas de phase spéciale)
        if compteur_actuel >= 4:
            libelle = 'Prix Gros'
        else:
            libelle = f'Prix upsell niveau {compteur_actuel}'
        couleur_classe = 'text-green-600'
        icone = 'fas fa-arrow-up'
    else:
        # PRIORITÉ 3: Prix normal par défaut
        libelle = 'Prix normal'
        couleur_classe = 'text-gray-600'
        icone = 'fas fa-tag'

    # Utiliser le sous-total réel du panier au lieu de recalculer
    # Cela garantit l'intégrité avec les données en base
    return {
        'prix_unitaire': float(sous_total_actuel / Decimal(str(quantite))),
        'sous_total': float(sous_total_actuel),
        'libelle': libelle,
        'couleur_classe': couleur_classe,
        'icone': icone,
        'est_remise': False
    }

@register.filter
def get_libelle_prix_contextuel(article, panier=None):
    """
    Retourne le libellé contextuel du prix selon les conditions de l'article et du panier.
    
    Args:
        article: L'objet Article
        panier: L'objet Panier (optionnel)
        
    Returns:
        dict: Informations contextuelles sur le prix
    """
    if not article:
        return {
            'libelle': 'Prix non défini',
            'couleur_classe': 'text-gray-500',
            'icone': 'fas fa-question'
        }
    
    # Si un panier est fourni, utiliser la logique de prix effectif
    if panier:
        prix_info = get_prix_effectif_panier(panier)
        return {
            'libelle': prix_info['libelle'],
            'couleur_classe': prix_info['couleur_classe'],
            'icone': prix_info['icone']
        }
    
    # Retour par défaut basé sur la phase de l'article
    return get_prix_affichage_remise(article, 1)

@register.filter
def has_prix_remise_disponible(article):
    """
    Vérifie si l'article a des prix de remise configurés.
    
    Returns:
        bool: True si au moins un prix de remise est défini
    """
    if not article:
        return False
    
    prix_remises = [
        getattr(article, 'prix_remise_1', None),
        getattr(article, 'prix_remise_2', None),
        getattr(article, 'prix_remise_3', None),
        getattr(article, 'prix_remise_4', None)
    ]
    
    return any(prix for prix in prix_remises if prix and prix > 0)

@register.filter
def get_meilleur_prix_remise(article):
    """
    Retourne le meilleur prix de remise disponible (le plus bas).
    
    Returns:
        dict: Informations sur le meilleur prix de remise
    """
    if not article or not has_prix_remise_disponible(article):
        return None
    
    prix_remises = []
    
    for niveau in [1, 2, 3, 4]:
        prix = get_prix_remise_applicable(article, niveau)
        if prix and prix > 0:
            prix_remises.append({
                'prix': prix,
                'niveau': niveau,
                'libelle': f'Prix remise {niveau}'
            })
    
    
    if not prix_remises:
        return None
    
    # Retourner le prix le plus bas
    meilleur_prix = min(prix_remises, key=lambda x: x['prix'])
    
    # Calculer l'économie
    economie_info = calcul_economie_remise(article, meilleur_prix['prix'])
    meilleur_prix.update(economie_info)
    
    return meilleur_prix