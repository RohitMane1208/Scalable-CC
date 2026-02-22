# verification/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # This will be: domain.com/api/email/
    path('email/', views.verify_email, name='verify_email'),
    
    # This will be: domain.com/api/status/
    path('status/', views.check_verification_status, name='check_status'),
    
    # This will be: domain.com/api/verify/<token>/
    path('verify/<uuid:token>/', views.verify_token, name='verify_token'),
]