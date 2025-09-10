from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages


def etiquettes_permission_required(permission):
    """
    Décorateur pour vérifier les permissions spécifiques aux étiquettes
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return render(request, 'etiquettes_pro/403.html', status=403)
            
            # Vérifier si l'utilisateur a la permission
            if not request.user.has_perm(f'etiquettes_pro.{permission}'):
                messages.error(request, 'Vous n\'avez pas les permissions nécessaires pour accéder à cette fonctionnalité.')
                return render(request, 'etiquettes_pro/403.html', {
                    'permission_required': permission,
                    'user_permissions': request.user.get_all_permissions()
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def superviseur_required(view_func):
    """
    Décorateur pour vérifier que l'utilisateur est un opérateur de supervision
    Compatible avec le décorateur de Superpreparation
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            from parametre.models import Operateur
            operateur = Operateur.objects.get(user=request.user, actif=True)
            
            # Autoriser uniquement les superviseurs et ADMIN
            if operateur.type_operateur in ['SUPERVISEUR_PREPARATION', 'ADMIN']:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Accès réservé aux opérateurs de supervision.')
                return render(request, 'etiquettes_pro/403.html', {
                    'message': 'Cette fonctionnalité est réservée aux opérateurs de supervision.',
                    'user_groups': [group.name for group in request.user.groups.all()],
                    'operateur_type': operateur.get_type_operateur_display()
                }, status=403)
                
        except Operateur.DoesNotExist:
            # Fallback si pas de profil: autoriser selon groupes Django (seulement superviseur)
            if request.user.groups.filter(name='superviseur').exists():
                return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Accès réservé aux opérateurs de supervision.')
            return render(request, 'etiquettes_pro/403.html', {
                'message': 'Cette fonctionnalité est réservée aux opérateurs de supervision.',
                'user_groups': [group.name for group in request.user.groups.all()]
            }, status=403)
    
    return wrapper


def can_manage_templates(view_func):
    """
    Décorateur pour vérifier la permission de gestion des templates
    """
    return etiquettes_permission_required('can_manage_etiquette_templates')(view_func)


def can_view_templates(view_func):
    """
    Décorateur pour vérifier la permission de visualisation des templates
    """
    return etiquettes_permission_required('can_view_etiquette_templates')(view_func)


def can_print_etiquettes(view_func):
    """
    Décorateur pour vérifier la permission d'impression des étiquettes
    """
    return etiquettes_permission_required('can_print_etiquettes')(view_func)
