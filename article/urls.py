from django.urls import path
from . import views

app_name = 'article'
 
urlpatterns = [
    # Pages principales
    path('', views.liste_articles, name='liste'),
    path('detail/<int:id>/', views.detail_article, name='detail'),
    path('modifier/<int:id>/', views.modifier_article, name='modifier'),
    path('creer/', views.creer_article, name='creer'),
    path('supprimer/<int:id>/', views.supprimer_article, name='supprimer'),
    path('supprimer-masse/', views.supprimer_articles_masse, name='supprimer_masse'),


    # Gestion des variantes d'articles
    path('variantes/', views.liste_variantes, name='liste_variantes'),
    path('variantes/creer-ajax/', views.creer_variantes_ajax, name='creer_variantes_ajax'),
    path('variantes/supprimer/<int:id>/', views.supprimer_variante, name='supprimer_variante'),
    path('variantes/supprimer-masse/', views.supprimer_variantes_masse, name='supprimer_variante_masse'),

    
    # Filtres par catégorie
    path('categorie/<str:categorie>/', views.articles_par_categorie, name='par_categorie'),
    
    # Gestion du stock
    path('stock-faible/', views.stock_faible, name='stock_faible'),
    path('rupture-stock/', views.rupture_stock, name='rupture_stock'),
    
    # Gestion des promotions
    path('promotions/', views.liste_promotions, name='liste_promotions'),
    path('promotions/creer/', views.creer_promotion, name='creer_promotion'),
    path('promotions/<int:id>/', views.detail_promotion, name='detail_promotion'),
    path('promotions/modifier/<int:id>/', views.modifier_promotion, name='modifier_promotion'),
    path('promotions/supprimer/<int:id>/', views.supprimer_promotion, name='supprimer_promotion'),
    path('promotions/activer-desactiver/<int:id>/', views.activer_desactiver_promotion, name='activer_desactiver_promotion'),
    path('promotions/gerer-automatiquement/', views.gerer_promotions_automatiquement, name='gerer_promotions_automatiquement'),
    
    # Gestion des phases
    path('changer-phase/<int:id>/', views.changer_phase, name='changer_phase'),
    path('appliquer-liquidation/<int:id>/', views.appliquer_liquidation, name='appliquer_liquidation'),
    path('reinitialiser-prix/<int:id>/', views.reinitialiser_prix, name='reinitialiser_prix'),
    
    # URLs pour la gestion des couleurs et pointures
    path('gestion-couleurs-pointures/', views.gestion_couleurs_pointures, name='gestion_couleurs_pointures'),
    path('pointures/creer/', views.creer_pointure, name='creer_pointure'),
    path('pointures/modifier/<int:pointure_id>/', views.modifier_pointure, name='modifier_pointure'),
    path('pointures/supprimer/<int:pointure_id>/', views.supprimer_pointure, name='supprimer_pointure'),

    path('gestion-articles/couleurs/creer/', views.creer_couleur, name='creer_couleur'),
    path('gestion-articles/couleurs/modifier/<int:couleur_id>/', views.modifier_couleur, name='modifier_couleur'),
    path('gestion-articles/couleurs/supprimer/<int:couleur_id>/', views.supprimer_couleur, name='supprimer_couleur'),
    
    # URLs pour la gestion des catégories
    path('categories/creer/', views.creer_categorie, name='creer_categorie'),
    path('categories/modifier/<int:categorie_id>/', views.modifier_categorie, name='modifier_categorie'),
    path('categories/supprimer/<int:categorie_id>/', views.supprimer_categorie, name='supprimer_categorie'),
    
    # URLs pour la gestion des genres
    path('genres/creer/', views.creer_genre, name='creer_genre'),
    path('genres/modifier/<int:genre_id>/', views.modifier_genre, name='modifier_genre'),
    path('genres/supprimer/<int:genre_id>/', views.supprimer_genre, name='supprimer_genre'),
] 