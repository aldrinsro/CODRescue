from django import template
from decimal import Decimal, ROUND_HALF_UP

register = template.Library()

@register.filter
def get_prix_affichage_remise(article, quantite=1):
    """
    Détermine le prix d'affichage selon la phase de l'article et les remises disponibles.
    Remplace les conditions complexes dans les templates.
    
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
    
    # Vérifier d'abord si un prix de remise est applicable
    # Les prix de remise ont priorité sur les upsells
    prix_remise_trouve = None
    for niveau in [1, 2, 3, 4]:
        prix_remise = get_prix_remise_applicable(article, niveau)
        if prix_remise and prix_remise > 0:
            prix_remise_trouve = {
                'prix': prix_remise,
                'libelle': f'Prix remise {niveau}',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'type': f'remise_{niveau}'
            }
            break
    
    if prix_remise_trouve:
        return prix_remise_trouve
    
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
    
    # Article upsell - gestion des prix par quantité (seulement si pas de remise)
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
            libelle = 'Prix upsell niveau 4'
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
        
    if niveau_remise == 'liquidation':
        return getattr(article, 'Prix_liquidation', None)
    elif niveau_remise == 1:
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
    
    # Vérifier si une remise a été explicitement appliquée
    if hasattr(panier, 'remise_appliquer') and panier.remise_appliquer:
        type_remise = getattr(panier, 'type_remise_appliquee', '')
        
        # Retourner le prix avec le libellé approprié selon le type de remise
        if type_remise == 'remise_1':
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix remise 1 appliquée',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'est_remise': True
            }
        elif type_remise == 'remise_2':
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix remise 2 appliquée',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'est_remise': True
            }
        elif type_remise == 'remise_3':
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix remise 3 appliquée',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'est_remise': True
            }
        elif type_remise == 'remise_4':
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix remise 4 appliquée',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'est_remise': True
            }
        elif type_remise == 'liquidation':
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix liquidation appliqué',
                'couleur_classe': 'text-red-600',
                'icone': 'fas fa-fire',
                'est_remise': True
            }
        else:
            # Remise personnalisée
            return {
                'prix_unitaire': float(prix_unitaire_effectif),
                'sous_total': float(sous_total_actuel),
                'libelle': 'Prix remisé (personnalisé)',
                'couleur_classe': 'text-purple-600',
                'icone': 'fas fa-percent',
                'est_remise': True
            }
    
    # Aucune remise appliquée - utiliser la logique standard
    prix_info_standard = get_prix_affichage_remise(article, quantite)
    prix_unitaire_standard = Decimal(str(prix_info_standard['prix']))
    
    return {
        'prix_unitaire': float(prix_unitaire_standard),
        'sous_total': float(prix_unitaire_standard * quantite),
        'libelle': prix_info_standard['libelle'],
        'couleur_classe': prix_info_standard['couleur_classe'],
        'icone': prix_info_standard['icone'],
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
        getattr(article, 'prix_remise_4', None),
        getattr(article, 'Prix_liquidation', None)
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
    
    # Ajouter prix de liquidation
    prix_liquidation = get_prix_remise_applicable(article, 'liquidation')
    if prix_liquidation and prix_liquidation > 0:
        prix_remises.append({
            'prix': prix_liquidation,
            'niveau': 'liquidation',
            'libelle': 'Prix liquidation'
        })
    
    if not prix_remises:
        return None
    
    # Retourner le prix le plus bas
    meilleur_prix = min(prix_remises, key=lambda x: x['prix'])
    
    # Calculer l'économie
    economie_info = calcul_economie_remise(article, meilleur_prix['prix'])
    meilleur_prix.update(economie_info)
    
    return meilleur_prix