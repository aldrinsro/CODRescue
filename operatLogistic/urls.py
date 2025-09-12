from django.urls import path
from . import views
from .service_apres_vente import views as sav_views
from .barre_recherche_globale import views as search_views
from . import articles_retournes_views

app_name = 'operatLogistic'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),

    path('parametre/', views.parametre, name='parametre'),
    path('profile/', views.profile_logistique, name='profile'),
    path('profile/modifier/', views.modifier_profile_logistique, name='modifier_profile'),
    path('commande/<int:commande_id>/probleme/', views.signaler_probleme, name='signaler_probleme'),
    # URL pour le SAV
    path('commande/<int:commande_id>/changer-etat-sav/', views.changer_etat_sav, name='changer_etat_sav'),
    path('commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles, name='rafraichir_articles'),
    # URLs pour les opérations sur les articles
    path('commande/<int:commande_id>/ajouter-article/', views.ajouter_article, name='ajouter_article'),
    path('commande/<int:commande_id>/modifier-quantite/', views.modifier_quantite_article, name='modifier_quantite_article'),

    # URL pour la livraison partielle
    path('commande/<int:commande_id>/livraison-partielle/', views.livraison_partielle, name='livraison_partielle'),
    # URL pour voir les commandes renvoyées en préparation
    # API pour les articles
    path('api/articles/', views.api_articles, name='api_articles'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande, name='api_panier_commande'),
   
    
    # URLs pour les listes SAV
    path('sav/reportees/', sav_views.commandes_reportees, name='commandes_reportees'),
    path('sav/livrees-partiellement/', sav_views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('sav/avec-changement/', sav_views.commandes_livrees_avec_changement, name='commandes_livrees_avec_changement'),
    path('sav/retournees/', sav_views.commandes_retournees, name='commandes_retournees'),
    path('sav/livrees/', sav_views.commandes_livrees, name='commandes_livrees'),
    path('sav/commande/<int:commande_id>/marquer-payee/', sav_views.marquer_commande_payee, name='marquer_commande_payee'),
    
    # URLs pour la recherche globale
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('recherche-globale/api/', search_views.global_search_api, name='global_search_api'),
    path('recherche-globale/suggestions/', search_views.search_suggestions_api, name='search_suggestions_api'),
    
    # URLs pour la gestion des articles retournés
    path('articles-retournes/', articles_retournes_views.liste_articles_retournes, name='liste_articles_retournes'),
    path('articles-retournes/<int:retour_id>/', articles_retournes_views.detail_article_retourne, name='detail_article_retourne'),
    path('articles-retournes/<int:retour_id>/traiter/', articles_retournes_views.traiter_article_retourne, name='traiter_article_retourne'),
    path('articles-retournes/reintegrer-automatique/', articles_retournes_views.reintegrer_automatique, name='reintegrer_automatique'),
    path('articles-retournes/statistiques/', articles_retournes_views.statistiques_retours, name='statistiques_retours'),
] 
