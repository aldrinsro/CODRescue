"""
Context processors pour le chatbot.
Injecte les informations utilisateur et interface dans tous les templates.
"""


def chatbot_context(request):
    """
    Injecte le contexte chatbot dans tous les templates.
    Permet d'avoir accès à l'interface active et aux infos utilisateur.
    """
    context = {
        'chatbot_interface': 'ADMIN',
        'chatbot_user_type': 'ANONYMOUS',
        'chatbot_user_name': 'Invité',
        'chatbot_user_id': None,
        'chatbot_operator_id': None,
    }

    # Détection de l'interface active depuis le chemin
    path = request.path_info
    referer = request.META.get('HTTP_REFERER', '')

    if 'operateur-confirme' in path or 'operateur-confirme' in referer:
        context['chatbot_interface'] = 'CONFIRMATION'
    elif 'operateur-preparation' in path or 'operateur-preparation' in referer:
        context['chatbot_interface'] = 'PREPARATION'
    elif 'operateur-logistique' in path or 'operateur-logistique' in referer:
        context['chatbot_interface'] = 'LOGISTIQUE'
    elif 'Superpreparation' in path or 'Superpreparation' in referer:
        context['chatbot_interface'] = 'SUPERVISION'
    elif 'parametre' in path or 'admin' in path:
        context['chatbot_interface'] = 'ADMIN'

    # Informations utilisateur si authentifié
    if request.user.is_authenticated:
        context['chatbot_user_id'] = request.user.id
        context['chatbot_user_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username

        # Récupérer le type d'opérateur
        try:
            from parametre.models import Operateur
            operateur = Operateur.objects.filter(user=request.user, actif=True).first()
            if operateur:
                context['chatbot_operator_id'] = operateur.id
                context['chatbot_user_type'] = operateur.type_operateur
                context['chatbot_user_name'] = f"{operateur.prenom} {operateur.nom}".strip()
            elif request.user.is_superuser:
                context['chatbot_user_type'] = 'ADMIN'
        except Exception:
            # En cas d'erreur, utiliser les valeurs par défaut
            if request.user.is_superuser:
                context['chatbot_user_type'] = 'ADMIN'

    return context


def get_interface_label(interface_type):
    """Retourne le libellé français de l'interface."""
    labels = {
        'CONFIRMATION': 'Confirmation',
        'PREPARATION': 'Préparation',
        'LOGISTIQUE': 'Logistique',
        'SUPERVISION': 'Supervision',
        'ADMIN': 'Administration',
    }
    return labels.get(interface_type, 'Non définie')


def get_interface_icon(interface_type):
    """Retourne l'icône associée à l'interface."""
    icons = {
        'CONFIRMATION': '✓',
        'PREPARATION': '📦',
        'LOGISTIQUE': '🚚',
        'SUPERVISION': '📊',
        'ADMIN': '⚙️',
    }
    return icons.get(interface_type, '💬')


def get_interface_color(interface_type):
    """Retourne la couleur associée à l'interface."""
    colors = {
        'CONFIRMATION': '#4CAF50',  # Vert
        'PREPARATION': '#FF9800',   # Orange
        'LOGISTIQUE': '#2196F3',    # Bleu
        'SUPERVISION': '#9C27B0',   # Violet
        'ADMIN': '#607D8B',         # Gris-bleu
    }
    return colors.get(interface_type, '#4CAF50')
