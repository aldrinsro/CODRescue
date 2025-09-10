"""
Vues de redirection pour l'accès direct aux étiquettes
"""

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import superviseur_required

@login_required
def redirect_to_etiquettes(request):
    """
    Redirection vers les étiquettes après login
    """
    # Vérifier si l'utilisateur a les permissions
    try:
        from parametre.models import Operateur
        operateur = Operateur.objects.get(user=request.user, actif=True)
        
        # Autoriser uniquement les superviseurs et ADMIN
        if operateur.type_operateur in ['SUPERVISEUR_PREPARATION', 'ADMIN']:
            return redirect('etiquettes_pro:dashboard')
        else:
            messages.error(request, 'Accès réservé aux opérateurs de supervision.')
            return redirect('Superpreparation:home')
            
    except:
        # Fallback si pas de profil: autoriser selon groupes Django (seulement superviseur)
        if request.user.groups.filter(name='superviseur').exists():
            return redirect('etiquettes_pro:dashboard')
        
        messages.error(request, 'Accès réservé aux opérateurs de supervision.')
        return redirect('Superpreparation:home')
