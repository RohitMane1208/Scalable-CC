from django.urls import path
from . import views

urlpatterns = [
    # Main entry point for passenger login and ticket booking
    path('', views.booking_page, name='booking'),
    
    # Passenger safety dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # --- Emergency Request Management ---
    # New: Route to cancel a specific active security request (Hospital/Police/Fire)
    path('cancel-request/<int:request_id>/', views.cancel_emergency_request, name='cancel_request'),

    # --- Ticket/Journey Management ---
    # Route to end journey and deactivate safety link
    path('cancel/<int:ticket_id>/', views.cancel_ticket, name='cancel_ticket'),
    
    # --- Identity & Verification ---
    # API for real-time email typo checking (AJAX)
    path('api/check-typo/', views.api_check_typo, name='check_typo'),
    
    # Target for the identity verification link sent via email
    path('verify/<uuid:token>/', views.verify_ticket_token, name='verify_ticket'),
]