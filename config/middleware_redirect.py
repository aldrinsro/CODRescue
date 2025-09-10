"""
Middleware pour gérer les redirections après login
"""

from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages

class RedirectAfterLoginMiddleware:
    """
    Middleware qui capture l'URL demandée et la stocke en session
    pour permettre la redirection après login
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur n'est pas connecté et essaie d'accéder à une page protégée
        if not request.user.is_authenticated:
            # Vérifier si c'est une page qui nécessite une authentification
            protected_paths = [
                '/etiquettes-pro/',
                '/Superpreparation/',
                '/operateur-preparation/',
                '/operateur-confirme/',
                '/operateur-logistique/',
                '/parametre/',
            ]
            
            # Vérifier si le chemin actuel commence par un des chemins protégés
            if any(request.path.startswith(path) for path in protected_paths):
                # Stocker l'URL demandée en session
                request.session['next_url'] = request.get_full_path()
        
        # Si l'utilisateur est connecté et essaie d'accéder aux étiquettes
        elif request.user.is_authenticated and request.path.startswith('/etiquettes-pro/'):
            # Vérifier les permissions
            try:
                from parametre.models import Operateur
                operateur = Operateur.objects.get(user=request.user, actif=True)
                
                # Autoriser uniquement les superviseurs et ADMIN
                if operateur.type_operateur not in ['SUPERVISEUR_PREPARATION', 'ADMIN']:
                    # Fallback: vérifier les groupes Django (seulement superviseur)
                    if not request.user.groups.filter(name='superviseur').exists():
                        messages.error(request, 'Accès réservé aux opérateurs de supervision.')
                        return redirect('Superpreparation:home')
                        
            except:
                # Fallback si pas de profil: autoriser selon groupes Django (seulement superviseur)
                if not request.user.groups.filter(name='superviseur').exists():
                    messages.error(request, 'Accès réservé aux opérateurs de supervision.')
                    return redirect('Superpreparation:home')
        
        response = self.get_response(request)
        return response
