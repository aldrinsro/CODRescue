from django.urls import path
from django.shortcuts import redirect
from . import views, views_retournee,views_articles
from .barre_recherche_globale import views as search_views
from operatConfirme import views as view_modif 

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
    


    #Gestion des commandes confirmees
    path('commandes-confirmees/', views.commandes_confirmees, name='commandes_confirmees'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),


    #gestion des API
    path('api/commande/<int:commande_id>/articles/', views.api_articles_commande, name='api_articles_commande'),
    path('api/commandes-confirmees/', views.api_commandes_confirmees, name='api_commandes_confirmees'),
    path('api/commande-info/<int:commande_id>/', views.api_commande_info, name='api_commande_info'),


 
    path('modifier-commande-superviseur/<int:commande_id>/', views.modifier_commande_superviseur, name='modifier_commande_superviseur'),
    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'),

    path('api/commande/<int:commande_id>/panier/<int:panier_id>/prix-remise/', view_modif.get_prix_remise_article, name='get_prix_remise_article'),
    path('api/panier/<int:panier_id>/activer-remise/', view_modif.activer_remise_panier, name='activer_remise_panier'),
    path('api/panier/<int:panier_id>/desactiver-remise/', view_modif.desactiver_remise_panier, name='desactiver_remise_panier'),
    







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
    path('commande/<int:commande_id>/diagnostiquer-compteur/', views_articles.diagnostiquer_compteur, name='diagnostiquer_compteur'),
    path('api/article/<int:article_id>/variantes/', views.get_article_variants, name='get_article_variants'),
    



    # URLs pour les modales d'impression
    path('api/ticket-commande-new/', views.api_ticket_commande_new, name='api_ticket_commande_new'),
    path('api/qr-codes-articles/', views.api_qr_codes_articles, name='api_qr_codes_articles'),
    path('api/finaliser-preparation/<int:commande_id>/', views.api_finaliser_preparation, name='api_finaliser_preparation'),






    # Gestion des envois
    path('envois/', views.envois_view, name='envois'),
    path('envois/historique/', views.historique_envois_view, name='historique_envois'),
    # Redirection pour l'ancienne URL
    path('historique-envois/', redirect_historique_envois, name='historique_envois_redirect'),
    path('envois/creer-region/', views.creer_envoi_region, name='creer_envoi_region'),
    path('envois/creer-multiples/', views.creer_envois_multiples, name='creer_envois_multiples'),
    path('envois/cloturer/', views.cloturer_envoi, name='cloturer_envoi'),
    path('envois/cloturer-multiples/', views.cloturer_envois_multiples, name='cloturer_envois_multiples'),
    path('envois/<int:envoi_id>/export-excel/', views.export_commandes_envoi_excel, name='export_commandes_envoi_excel'),
    path('envois/<int:envoi_id>/commandes/', views.commandes_envoi, name='commandes_envoi'),
    path('envois/<int:envoi_id>/commandes-historique/', views.commandes_envoi_historique, name='commandes_envoi_historique'),



    
    # === NOUVELLES URLs : EXPORTS CONSOLIDÉS ===
 



    # === URLs RECHERCHE GLOBALE ===
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('api/recherche-globale/', search_views.global_search_api, name='global_search_api'),
    path('api/suggestions-recherche/', search_views.search_suggestions_api, name='search_suggestions_api'),


    # === NOUVELLES URLs : GESTION DES PROMOTIONS (SUPERPREPARATION) === 
    # Pages principales des promotions
    path('promotions/', views_articles.liste_promotions, name='liste_promotions'),
    path('promotions/creer/', views_articles.creer_promotion, name='creer_promotion'),
    path('promotions/<int:id>/', views_articles.detail_promotion, name='detail_promotion'),
    path('promotions/modifier/<int:id>/', views_articles.modifier_promotion, name='modifier_promotion'),
    path('promotions/supprimer/<int:id>/', views_articles.supprimer_promotion, name='supprimer_promotion'),
    path('promotions/activer-desactiver/<int:id>/', views_articles.activer_desactiver_promotion, name='activer_desactiver_promotion'),
    path('promotions/gerer-automatiquement/', views_articles.gerer_promotions_automatiquement, name='gerer_promotions_automatiquement'),
    
    # === NOUVELLES URLs : GESTION DES ARTICLES STOCK (SUPERPREPARATION) === 
    # Pages principales
    path('gestion-articles/', views_articles.liste_articles, name='liste_articles'),
    # Redirection pour compatibilité avec l'ancienne URL
    path('articles/', views_articles.liste_articles, name='liste_articles_redirect'),
    path('gestion-articles/detail/<int:id>/', views_articles.detail_article, name='detail_article'),
    path('gestion-articles/modifier/<int:id>/', views_articles.modifier_article, name='modifier_article'),
    path('gestion-articles/creer/', views_articles.creer_article, name='creer_article'),
    path('gestion-articles/supprimer/<int:id>/', views_articles.supprimer_article, name='supprimer_article'),
    path('gestion-articles/supprimer-masse/', views_articles.supprimer_articles_masse, name='supprimer_masse'),


    # Gestion des variantes d'articles
    path('gestion-articles/variantes/', views_articles.liste_variantes, name='liste_variantes'),
    path('gestion-articles/variantes/creer-ajax/', views_articles.creer_variantes_ajax, name='creer_variantes_ajax'),
    path('gestion-articles/variantes/supprimer/<int:id>/', views_articles.supprimer_variante, name='supprimer_variante'),
    path('gestion-articles/variantes/supprimer-masse/', views_articles.supprimer_variantes_masse, name='supprimer_variante_masse'),

    
    # Filtres par catégorie
    path('gestion-articles/categorie/<str:categorie>/', views_articles.articles_par_categorie, name='par_categorie'),
    
    # Gestion du stock
    path('gestion-articles/stock-faible/', views_articles.stock_faible, name='stock_faible'),
    path('gestion-articles/rupture-stock/', views_articles.rupture_stock, name='rupture_stock'),
    # Alias pour compatibilité avec anciens liens
    path('gestion-articles/alertes-stock/', views_articles.stock_faible, name='alertes_stock'),
    
    # Gestion des phases
    path('gestion-articles/changer-phase/<int:id>/', views_articles.changer_phase, name='changer_phase'),
    path('gestion-articles/appliquer-liquidation/<int:id>/', views_articles.appliquer_liquidation, name='appliquer_liquidation'),
    path('gestion-articles/appliquer-liquidation-prix-db/<int:id>/', views_articles.appliquer_liquidation_prix_db, name='appliquer_liquidation_prix_db'),
    path('gestion-articles/reinitialiser-prix/<int:id>/', views_articles.reinitialiser_prix, name='reinitialiser_prix'),
    
    # URLs pour la gestion des couleurs et pointures
    path('gestion-articles/gestion-couleurs-pointures/', views_articles.gestion_couleurs_pointures, name='gestion_couleurs_pointures'),
    path('gestion-articles/pointures/creer/', views_articles.creer_pointure, name='creer_pointure'),
    path('gestion-articles/pointures/modifier/<int:pointure_id>/', views_articles.modifier_pointure, name='modifier_pointure'),
    path('gestion-articles/pointures/supprimer/<int:pointure_id>/', views_articles.supprimer_pointure, name='supprimer_pointure'),

    path('gestion-articles/couleurs/creer/', views_articles.creer_couleur, name='creer_couleur'),
    path('gestion-articles/couleurs/modifier/<int:couleur_id>/', views_articles.modifier_couleur, name='modifier_couleur'),
    path('gestion-articles/couleurs/supprimer/<int:couleur_id>/', views_articles.supprimer_couleur, name='supprimer_couleur'),
    
    # URLs pour la gestion des catégories
    path('gestion-articles/categories/creer/', views_articles.creer_categorie, name='creer_categorie'),
    path('gestion-articles/categories/modifier/<int:categorie_id>/', views_articles.modifier_categorie, name='modifier_categorie'),
    path('gestion-articles/categories/supprimer/<int:categorie_id>/', views_articles.supprimer_categorie, name='supprimer_categorie'),
    
    # URLs pour la gestion des genres
    path('gestion-articles/genres/creer/', views_articles.creer_genre, name='creer_genre'),
    path('gestion-articles/genres/modifier/<int:genre_id>/', views_articles.modifier_genre, name='modifier_genre'),
    path('gestion-articles/genres/supprimer/<int:genre_id>/', views_articles.supprimer_genre, name='supprimer_genre'),

    # === NOUVELLES URLs : SERVICE - GESTION DES ARTICLES RETOURNÉS ===
    # Pages principales du service
    path('service/articles-retournes/', views_retournee.liste_articles_retournes_service, name='service_liste_articles_retournes'),
    path('service/articles-retournes/<int:retour_id>/', views_retournee.detail_article_retourne_service, name='service_detail_article_retourne'),
    path('service/articles-retournes/statistiques/', views_retournee.statistiques_retours_service, name='service_statistiques_retours'),

    # APIs pour le traitement des articles retournés
    path('service/api/traiter-article-retourne/<int:retour_id>/', views_retournee.traiter_article_retourne_service, name='service_traiter_article_retourne'),
    path('service/api/reintegrer-automatique/', views_retournee.reintegrer_automatique_service, name='service_reintegrer_automatique'),
    path('service/api/articles-retournes-modal/', views_retournee.api_articles_retournes_modal, name='service_api_articles_retournes_modal'),


]
