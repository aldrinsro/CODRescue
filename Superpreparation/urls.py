from django.urls import path
from django.shortcuts import redirect
from . import views
from .barre_recherche_globale import views as search_views

app_name = 'Superpreparation'

# Fonction de redirection pour l'ancienne URL
def redirect_historique_envois(request):
    return redirect('Superpreparation:historique_envois')

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_redirect'),

     #Gestion des commandes 
    path('liste-prepa/', views.liste_prepa, name='liste_prepa'),
    path('commandes-en-preparation/', views.commandes_en_preparation, name='commandes_en_preparation'),
    path('commandes-emballees/', views.commandes_emballees, name='commandes_emballees'),
    path('commandes-preparees/', views.commandes_preparees, name='commandes_preparees'),


   
    path('commandes-confirmees/', views.commandes_confirmees, name='commandes_confirmees'),
    path('livrees-partiellement/', views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('retournees/', views.commandes_retournees, name='commandes_retournees'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),



    path('api/commande/<int:commande_id>/articles/', views.api_articles_commande, name='api_articles_commande'),
    path('api/commandes-confirmees/', views.api_commandes_confirmees, name='api_commandes_confirmees'),
    path('api/commande-info/<int:commande_id>/', views.api_commande_info, name='api_commande_info'),
    # Impression supprimée (gérée par Gestion des étiquettes)
    path('modifier-commande/<int:commande_id>/', views.modifier_commande_prepa, name='modifier_commande'),
    path('modifier-commande-superviseur/<int:commande_id>/', views.modifier_commande_superviseur, name='modifier_commande_superviseur'),
   
    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'),
    # path('api/commande/<int:commande_id>/changer-etat/', views.api_changer_etat_preparation, name='api_changer_etat_preparation') # Supprimée - plus nécessaire
    path('api/articles-disponibles-prepa/', views.api_articles_disponibles_prepa, name='api_articles_disponibles_prepa'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande_prepa, name='api_panier_commande'),
    path('api/commande/<int:commande_id>/panier-modal/', views.api_panier_commande, name='api_panier_commande_modal'),
    path('api/commande/<int:commande_id>/finaliser/', views.api_finaliser_commande, name='api_finaliser_commande'),
    path('api/commande/<int:commande_id>/panier-livraison/', views.api_panier_commande_livraison, name='api_panier_commande_livraison'),
    path('api/commande/<int:commande_id>/articles-livree-partiellement/', views.api_articles_commande_livree_partiellement, name='api_articles_commande_livree_partiellement'),
    path('api/traiter-commande-retournee/<int:commande_id>/', views.traiter_commande_retournee_api, name='traiter_commande_retournee_api'),


    # URLs pour la gestion des articles pendant la préparation
    path('commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles_commande_prepa, name='rafraichir_articles_commande_prepa'),
    path('commande/<int:commande_id>/ajouter-article/', views.ajouter_article_commande_prepa, name='ajouter_article_commande_prepa'),
    path('commande/<int:commande_id>/modifier-quantite/', views.modifier_quantite_article_prepa, name='modifier_quantite_article_prepa'),
    path('commande/<int:commande_id>/supprimer-article/', views.supprimer_article_commande_prepa, name='supprimer_article_commande_prepa'),
    path('commande/<int:commande_id>/prix-upsell/', views.api_prix_upsell_articles, name='api_prix_upsell_articles'),
    path('api/article/<int:article_id>/variantes/', views.get_article_variants, name='get_article_variants'),
    
    # URLs pour les modales d'impression
    path('api/codes-barres-commandes/', views.api_codes_barres_commandes, name='api_codes_barres_commandes'),
    path('api/ticket-commande/', views.api_ticket_commande, name='api_ticket_commande'),
    path('api/ticket-commande-multiple/', views.api_ticket_commande_multiple, name='api_ticket_commande_multiple'),
    path('api/etiquettes-articles/', views.api_etiquettes_articles, name='api_etiquettes_articles'),
    path('api/etiquettes-articles-multiple/', views.api_etiquettes_articles_multiple, name='api_etiquettes_articles_multiple'),
    path('api/finaliser-preparation/<int:commande_id>/', views.api_finaliser_preparation, name='api_finaliser_preparation'),

    # Gestion des envois
    path('envois/', views.envois_view, name='envois'),
    path('envois/historique/', views.historique_envois_view, name='historique_envois'),
    # Redirection pour l'ancienne URL
    path('historique-envois/', redirect_historique_envois, name='historique_envois_redirect'),
    path('envois/creer-region/', views.creer_envoi_region, name='creer_envoi_region'),
    path('envois/cloturer/', views.cloturer_envoi, name='cloturer_envoi'),
    path('envois/<int:envoi_id>/export-excel/', views.export_commandes_envoi_excel, name='export_commandes_envoi_excel'),
    path('envois/<int:envoi_id>/commandes/', views.commandes_envoi, name='commandes_envoi'),
    path('envois/<int:envoi_id>/commandes-historique/', views.commandes_envoi_historique, name='commandes_envoi_historique'),



    
    # === NOUVELLES URLs : EXPORTS CONSOLIDÉS ===
 



    # === URLs RECHERCHE GLOBALE ===
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('api/recherche-globale/', search_views.global_search_api, name='global_search_api'),
    path('api/suggestions-recherche/', search_views.search_suggestions_api, name='search_suggestions_api'),


    # === Urls des Gestions des Articles Stock === 


     # Pages principales
    path('articles/', views.liste_articles, name='liste_articles'),
    path('articles/detail/<int:id>/', views.detail_article, name='detail_article'),
    path('articles/modifier/<int:id>/', views.modifier_article, name='modifier_article'),
    path('articles/creer/', views.creer_article, name='creer_article'),
    path('articles/supprimer/<int:id>/', views.supprimer_article, name='supprimer_article'),
    path('articles/supprimer-masse/', views.supprimer_articles_masse, name='supprimer_masse'),


    # Gestion des variantes d'articles
    path('articles/variantes/', views.liste_variantes, name='liste_variantes'),
    path('articles/variantes/creer-ajax/', views.creer_variantes_ajax, name='creer_variantes_ajax'),
    path('variantes/supprimer/<int:id>/', views.supprimer_variante, name='supprimer_variante'),

    
    # Filtres par catégorie
    path('articles/categorie/<str:categorie>/', views.articles_par_categorie, name='par_categorie'),
    
    # Gestion du stock
    path('articles/stock-faible/', views.stock_faible, name='stock_faible'),
    path('articles/rupture-stock/', views.rupture_stock, name='rupture_stock'),
    
    # Gestion des promotions
    path('articles/promotions/', views.liste_promotions, name='liste_promotions'),
    path('articles/promotions/creer/', views.creer_promotion, name='creer_promotion'),
    path('articles/promotions/<int:id>/', views.detail_promotion, name='detail_promotion'),
    path('articles/promotions/modifier/<int:id>/', views.modifier_promotion, name='modifier_promotion'),
    path('articles/promotions/supprimer/<int:id>/', views.supprimer_promotion, name='supprimer_promotion'),
    path('articles/promotions/activer-desactiver/<int:id>/', views.activer_desactiver_promotion, name='activer_desactiver_promotion'),
    path('articles/promotions/gerer-automatiquement/', views.gerer_promotions_automatiquement, name='gerer_promotions_automatiquement'),
    
    # Gestion des phases
    path('articles/changer-phase/<int:id>/', views.changer_phase, name='changer_phase'),
    path('articles/appliquer-liquidation/<int:id>/', views.appliquer_liquidation, name='appliquer_liquidation'),
    path('reinitialiser-prix/<int:id>/', views.reinitialiser_prix, name='reinitialiser_prix'),
    
    # URLs pour la gestion des couleurs et pointures
    path('articles/gestion-couleurs-pointures/', views.gestion_couleurs_pointures, name='gestion_couleurs_pointures'),
    path('articles/pointures/creer/', views.creer_pointure, name='creer_pointure'),
    path('articles/pointures/modifier/<int:pointure_id>/', views.modifier_pointure, name='modifier_pointure'),
    path('articles/pointures/supprimer/<int:pointure_id>/', views.supprimer_pointure, name='supprimer_pointure'),

    path('articles/ gestion-articles/couleurs/creer/', views.creer_couleur, name='creer_couleur'),
    path('articles/gestion-articles/couleurs/modifier/<int:couleur_id>/', views.modifier_couleur, name='modifier_couleur'),
    path('articles/gestion-articles/couleurs/supprimer/<int:couleur_id>/', views.supprimer_couleur, name='supprimer_couleur'),
    
    # URLs pour la gestion des catégories
    path('articles/categories/creer/', views.creer_categorie, name='creer_categorie'),
    path('articles/categories/modifier/<int:categorie_id>/', views.modifier_categorie, name='modifier_categorie'),
    path('articles/categories/supprimer/<int:categorie_id>/', views.supprimer_categorie, name='supprimer_categorie'),
    
    # URLs pour la gestion des genres
    path('articles/genres/creer/', views.creer_genre, name='creer_genre'),
    path('articles/genres/modifier/<int:genre_id>/', views.modifier_genre, name='modifier_genre'),
    path('articles/genres/supprimer/<int:genre_id>/', views.supprimer_genre, name='supprimer_genre'),


   

]
