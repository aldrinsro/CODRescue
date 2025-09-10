from django.urls import path, include
from . import views
from . import views_redirect

app_name = 'etiquettes_pro'

urlpatterns = [
    # Dashboard
    path('', views.etiquettes_dashboard, name='dashboard'),
    
    # Redirection après login
    path('redirect/', views_redirect.redirect_to_etiquettes, name='redirect_after_login'),
    
    # Templates
    path('templates/', views.EtiquetteTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.create_template, name='template_create'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.edit_template, name='template_edit'),
    path('templates/<int:pk>/delete/', views.delete_template, name='template_delete'),
    
    # Étiquettes
    path('etiquettes/', views.etiquette_list, name='etiquette_list'),
    path('etiquettes/<int:etiquette_id>/preview/', views.preview_etiquette, name='etiquette_preview'),
    path('etiquettes/<int:etiquette_id>/print-data/', views.etiquette_print_data, name='etiquette_print_data'),
    path('etiquettes/<int:etiquette_id>/delete/', views.delete_etiquette, name='delete_etiquette'),
    path('etiquettes/<int:etiquette_id>/qr-codes/', views.generate_qr_codes_articles, name='generate_qr_codes_articles'),
    path('etiquettes/<int:etiquette_id>/qr-codes-simple/', views.generate_qr_codes_simple, name='generate_qr_codes_simple'),
    path('bulk-print-qr-codes-simple/', views.bulk_print_qr_codes_simple, name='bulk_print_qr_codes_simple'),
    path('bulk-print-qr-codes-details/', views.bulk_print_qr_codes_details, name='bulk_print_qr_codes_details'),
    path('templates/<int:template_id>/update-print-settings/', views.update_template_print_settings, name='update_template_print_settings'),
    path('barcode/<str:code_data>/', views.generate_barcode_image, name='generate_barcode_image'),
    path('qrcode/<str:code_data>/', views.generate_qrcode_image, name='generate_qrcode_image'),
    
    
    # API endpoints
    path('api/templates/', views.api_template_list, name='api_template_list'),
    path('api/etiquettes/', views.api_etiquette_list, name='api_etiquette_list'),
    path('api/commandes-with-paniers/', views.get_commandes_with_paniers, name='get_commandes_with_paniers'),
    path('generate-etiquettes-manually/', views.generate_etiquettes_manually, name='generate_etiquettes_manually'),
    
    # API pour la gestion des statuts d'impression
    path('api/etiquettes/<int:etiquette_id>/mark-printed/', views.mark_etiquette_as_printed, name='mark_etiquette_as_printed'),
    path('api/etiquettes/mark-multiple-printed/', views.mark_multiple_etiquettes_as_printed, name='mark_multiple_etiquettes_as_printed'),
    path('api/statistics/', views.get_etiquettes_statistics, name='get_etiquettes_statistics'),
    
    # Test: Incrémenter les compteurs
    path('api/etiquettes/<int:etiquette_id>/test-increment/', views.test_increment_counters, name='test_increment_counters'),
]
