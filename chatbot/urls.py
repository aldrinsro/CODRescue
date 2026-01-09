from django.urls import path
from . import views, views_sync

urlpatterns = [
    # Endpoint minimal pour le chatbot version page unique
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/chatbot/data/', views.chatbot_data, name='chatbot_data'),
    path('api/sync/', views_sync.sync_data, name='chatbot_sync'),
]
