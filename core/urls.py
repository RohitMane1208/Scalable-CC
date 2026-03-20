from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_page, name='booking'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # New: Secure route to end journey and deactivate safety link
    # We use <uuid:ticket_id> to match the unique ID format of your Ticket model
    path('cancel/<int:ticket_id>/', views.cancel_ticket, name='cancel_ticket'),

    path('api/check-typo/', views.api_check_typo, name='check_typo'),
    
    # This matches the link your API will send: http://.../verify/<uuid>/
    path('verify/<uuid:token>/', views.verify_ticket_token, name='verify_ticket'),
]