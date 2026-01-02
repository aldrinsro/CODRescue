"""
================================================================================
EXEMPLE DE CONFIGURATION DES URLS - Module Common
================================================================================

Ce fichier montre comment configurer les URLs dans votre application
pour utiliser les handlers et APIs du module common.

Vous pouvez copier ces exemples dans votre app/urls.py et les adapter.

@version 1.0
@author YZ-RESCUE
"""

from django.urls import path
from django.contrib.auth.decorators import login_required

# ==============================================================================
# OPTION 1: VUE PRINCIPALE AVEC HANDLERS (RECOMMANDÉ)
# ==============================================================================

"""
Cette approche centralise toutes les actions dans une seule vue principale.
C'est la méthode recommandée car elle offre plus de contrôle et flexibilité.
"""

from . import views  # Vos vues locales

urlpatterns = [
    # Vue principale qui gère tous les handlers
    path('commandes/<int:commande_id>/modifier/',
         login_required(views.modifier_commande),
         name='modifier_commande'),

    # APIs pour les données et rafraîchissement
    path('api/articles-disponibles/',
         login_required(views.api_articles_disponibles_view),
         name='api_articles_disponibles'),

    path('get-article-variants/<int:article_id>/',
         login_required(views.get_article_variants_view),
         name='get_article_variants'),

    path('api/commande/<int:commande_id>/rafraichir-articles/',
         login_required(views.rafraichir_articles_view),
         name='rafraichir_articles'),

    path('calculer-remise-preview/<int:panier_id>/',
         login_required(views.calculer_remise_preview_view),
         name='calculer_remise_preview'),

    path('appliquer-remise/<int:panier_id>/',
         login_required(views.appliquer_remise_view),
         name='appliquer_remise'),

    path('retirer-remise/<int:panier_id>/',
         login_required(views.retirer_remise_view),
         name='retirer_remise'),
]


# ==============================================================================
# VIEWS.PY CORRESPONDANT (à créer dans votre app/views.py)
# ==============================================================================

"""
# Dans votre app/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from commande.models import Commande, Panier
from operateur.models import Operateur

# Import des handlers depuis common
from common.views.article_handlers import (
    handle_add_article,
    handle_delete_article,
    handle_update_quantity
)
from common.views.client_livraison_handlers import (
    handle_save_client_info,
    handle_save_livraison,
    handle_toggle_frais_livraison
)
from common.views.operation_handlers import (
    handle_create_operation,
    handle_update_operation,
    handle_delete_operation
)

# Import des APIs depuis common
from common.api.article_api import (
    api_articles_disponibles,
    get_article_variants,
    rafraichir_articles_section
)
from common.api.remise_api import (
    appliquer_remise_panier,
    retirer_remise_panier,
    calculer_remise_panier_preview
)


# -----------------------------------------------------------------------------
# VUE PRINCIPALE
# -----------------------------------------------------------------------------

@login_required
def modifier_commande(request, commande_id):
    '''
    Vue principale de modification de commande.
    Route toutes les actions AJAX vers les handlers appropriés.
    '''
    commande = get_object_or_404(Commande, id=commande_id)

    # Récupérer l'opérateur (adapter selon votre logique)
    try:
        operateur = Operateur.objects.get(
            user=request.user,
            type_operateur__in=['CONFIRMATION', 'PREPARATION', 'SAV']
        )
    except Operateur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Profil opérateur non trouvé'
        }, status=403)

    # Traitement des requêtes POST (AJAX)
    if request.method == 'POST':
        action = request.POST.get('action')

        # ===== GESTION DES ARTICLES =====
        if action == 'add_article':
            return handle_add_article(request, commande, operateur)

        elif action == 'delete_panier':
            return handle_delete_article(request, commande, operateur)

        elif action == 'update_quantity':
            return handle_update_quantity(request, commande, operateur)

        # ===== GESTION CLIENT/LIVRAISON =====
        elif action == 'save_client_info':
            return handle_save_client_info(request, commande, operateur)

        elif action == 'save_livraison':
            return handle_save_livraison(request, commande, operateur)

        elif action == 'toggle_frais_livraison':
            return handle_toggle_frais_livraison(request, commande, operateur)

        # ===== GESTION DES OPÉRATIONS =====
        elif action == 'create_operation':
            return handle_create_operation(request, commande, operateur)

        elif action == 'update_operation':
            return handle_update_operation(request, commande, operateur)

        elif action == 'delete_operation':
            return handle_delete_operation(request, commande, operateur)

        # Action inconnue
        else:
            return JsonResponse({
                'success': False,
                'error': f'Action inconnue: {action}'
            }, status=400)

    # GET: Afficher le formulaire de modification
    context = {
        'commande': commande,
        'operateur': operateur,
        # Ajouter d'autres données nécessaires pour le template
    }

    return render(request, 'votre_app/modifier_commande.html', context)


# -----------------------------------------------------------------------------
# WRAPPERS POUR LES APIs (injecter l'opérateur si nécessaire)
# -----------------------------------------------------------------------------

@login_required
def api_articles_disponibles_view(request):
    '''Wrapper pour l'API articles disponibles'''
    return api_articles_disponibles(request)


@login_required
def get_article_variants_view(request, article_id):
    '''Wrapper pour l'API variantes d'articles'''
    return get_article_variants(request, article_id)


@login_required
def rafraichir_articles_view(request, commande_id):
    '''Wrapper pour l'API rafraîchissement articles'''
    # Optionnel: spécifier un template custom
    # return rafraichir_articles_section(
    #     request,
    #     commande_id,
    #     template_path='votre_app/partials/_articles_section.html'
    # )
    return rafraichir_articles_section(request, commande_id)


@login_required
def calculer_remise_preview_view(request, panier_id):
    '''Wrapper pour l'API preview remise'''
    return calculer_remise_panier_preview(request, panier_id)


@login_required
def appliquer_remise_view(request, panier_id):
    '''Wrapper pour l'API application remise'''
    # Récupérer l'opérateur
    try:
        operateur = Operateur.objects.get(user=request.user)
    except Operateur.DoesNotExist:
        operateur = None

    return appliquer_remise_panier(request, panier_id, operateur)


@login_required
def retirer_remise_view(request, panier_id):
    '''Wrapper pour l'API retrait remise'''
    # Récupérer l'opérateur
    try:
        operateur = Operateur.objects.get(user=request.user)
    except Operateur.DoesNotExist:
        operateur = None

    return retirer_remise_panier(request, panier_id, operateur)
"""


# ==============================================================================
# OPTION 2: URLs DIRECTES VERS LES APIs (Alternative)
# ==============================================================================

"""
Cette approche route directement vers les APIs du module common.
Moins de contrôle mais configuration plus simple.

⚠️ Attention: Vous devrez créer des wrappers pour injecter l'opérateur.
"""

from common.api.article_api import (
    api_articles_disponibles,
    get_article_variants,
    rafraichir_articles_section
)
from common.api.remise_api import (
    appliquer_remise_panier,
    retirer_remise_panier,
    calculer_remise_panier_preview
)

# urlpatterns = [
#     # APIs Articles
#     path('api/articles-disponibles/',
#          login_required(api_articles_disponibles),
#          name='api_articles_disponibles'),
#
#     path('get-article-variants/<int:article_id>/',
#          login_required(get_article_variants),
#          name='get_article_variants'),
#
#     path('api/commande/<int:commande_id>/rafraichir-articles/',
#          login_required(rafraichir_articles_section),
#          name='rafraichir_articles'),
#
#     # APIs Remises (nécessitent des wrappers pour l'opérateur)
#     path('calculer-remise-preview/<int:panier_id>/',
#          login_required(calculer_remise_panier_preview),
#          name='calculer_remise_preview'),
#
#     # Attention: Ces deux APIs nécessitent un opérateur
#     # Il faut créer des wrappers comme dans l'Option 1
#     # path('appliquer-remise/<int:panier_id>/', ..., name='appliquer_remise'),
#     # path('retirer-remise/<int:panier_id>/', ..., name='retirer_remise'),
# ]


# ==============================================================================
# CONFIGURATION DU TEMPLATE
# ==============================================================================

"""
Dans votre template HTML, injecter les URLs pour que le JavaScript les utilise:

<!-- votre_app/templates/votre_app/modifier_commande.html -->

{% load static %}

<!-- Injection des URLs pour le JavaScript -->
<script>
    // ID de la commande pour les appels AJAX
    window.commandeId = {{ commande.id }};

    // URL principale de modification
    window.urlModifier = "{% url 'votre_app:modifier_commande' commande.id %}";

    // URLs des APIs (optionnel si vous utilisez des URLs hardcodées)
    window.urlApiArticles = "{% url 'votre_app:api_articles_disponibles' %}";
    window.urlRafraichir = "{% url 'votre_app:rafraichir_articles' commande.id %}";

    // Nom de l'app pour construire les URLs dynamiquement (optionnel)
    window.appName = 'votre-app';
</script>

<!-- Chargement des fichiers JavaScript globaux -->
<script src="{% static 'js/Commande/gestion_articles.js' %}"></script>
<script src="{% static 'js/Commande/remise.js' %}"></script>
<script src="{% static 'js/Commande/confirmation.js' %}"></script>
<script src="{% static 'js/Commande/detail_toggle.js' %}"></script>

<!-- Inclusion du template de section articles -->
<div id="mainContent" data-commande-id="{{ commande.id }}">
    {% include 'common/commande/section_articles.html' with commande=commande %}
</div>
"""


# ==============================================================================
# NOTES IMPORTANTES
# ==============================================================================

"""
1. CSRF Token:
   - Tous les appels AJAX POST doivent inclure le token CSRF
   - Le JavaScript utilise getCookie('csrftoken')
   - Assurez-vous que {% csrf_token %} est dans votre template

2. Authentification:
   - Toutes les vues doivent être protégées avec @login_required
   - Les APIs vérifient généralement l'accès dans le code

3. Permissions:
   - Adaptez la vérification de l'opérateur selon vos besoins
   - Exemple: type_operateur__in=['CONFIRMATION', 'PREPARATION', 'SAV']

4. Templates:
   - Les templates globaux sont dans templates/common/commande/
   - Vous pouvez créer vos propres templates et les passer en paramètre

5. URLs hardcodées:
   - Les fichiers JS ont des URLs hardcodées pour operateur-confirme
   - Utilisez window.urlModifier pour les surcharger (voir template ci-dessus)
   - Ou modifiez les fonctions getUrlModifier() dans le JS

6. Testing:
   - Testez chaque action AJAX individuellement
   - Vérifiez les logs backend pour les erreurs
   - Utilisez la console du navigateur pour débugger
"""


# ==============================================================================
# CHECKLIST D'INTÉGRATION
# ==============================================================================

"""
□ Copier ce fichier dans votre app et l'adapter
□ Créer les vues wrapper dans votre views.py
□ Configurer les URLs dans votre app/urls.py
□ Copier les templates de common/commande/ (ou créer les vôtres)
□ Copier les fichiers JS de static/js/Commande/
□ Ajouter les scripts dans votre template
□ Injecter les URLs JavaScript dans le template
□ Tester chaque fonctionnalité AJAX :
  □ Chargement des articles
  □ Ajout d'article
  □ Suppression d'article
  □ Modification de quantité
  □ Rafraîchissement de la section
  □ Aperçu de remise
  □ Application de remise
  □ Retrait de remise
  □ Sauvegarde client
  □ Sauvegarde livraison
  □ Toggle frais de livraison
  □ Opérations (create/update/delete)
□ Vérifier les logs pour les erreurs
□ Valider avec différents types d'opérateurs
"""

# ==============================================================================
# SUPPORT
# ==============================================================================

"""
Pour plus d'informations:
- Voir common/AJAX_MAPPING.md pour le mapping complet
- Voir common/README.md pour la documentation générale
- Voir static/js/Commande/QUICK_START.md pour le guide JavaScript
- Voir common/MIGRATION_GUIDE.md pour les détails techniques

Version: 1.0
Date: 2 Janvier 2026
Auteur: YZ-RESCUE
"""
