from django.urls import path
from . import views
from .barre_recherche_globale import views as search_views

app_name = 'Prepacommande'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_redirect'),
    path('liste-prepa/', views.liste_prepa, name='liste_prepa'),
    path('en-preparation/', views.commandes_en_preparation, name='commandes_en_preparation'),
    path('livrees-partiellement/', views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('retournees/', views.commandes_retournees, name='commandes_retournees'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),
  
    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'), 
    path('api/articles-disponibles-prepa/', views.api_articles_disponibles_prepa, name='api_articles_disponibles_prepa'),
    path('api/panier/<int:commande_id>/', views.api_panier_modal, name='api_panier_modal'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande_prepa, name='api_panier_commande'),
    path('api/commande/<int:commande_id>/panier-livraison/', views.api_panier_commande_livraison, name='api_panier_commande_livraison'),
    path('api/commande/<int:commande_id>/articles-livree-partiellement/', views.api_articles_commande_livree_partiellement, name='api_articles_commande_livree_partiellement'),
    path('api/traiter-commande-retournee/<int:commande_id>/', views.traiter_commande_retournee_api, name='traiter_commande_retournee_api'),
    path('api/changer-etat-commande/<int:commande_id>/', views.api_changer_etat_commande, name='api_changer_etat_commande'),
   
    # URLs pour la gestion des articles pendant la préparation
    path('commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles_commande_prepa, name='rafraichir_articles_commande_prepa'),

    path('commande/<int:commande_id>/prix-upsell/', views.api_prix_upsell_articles, name='api_prix_upsell_articles'),

    # URLs pour la recherche globale
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('recherche-globale/api/', search_views.global_search_api, name='global_search_api'),
    path('recherche-globale/suggestions/', search_views.search_suggestions_api, name='search_suggestions_api'),
] 