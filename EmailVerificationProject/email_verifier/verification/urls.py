from django.urls import path
from . import views

urlpatterns = [
    path('email/', views.verify_email, name='verify_email'),
    
    path('status/', views.check_verification_status, name='check_status'),
    
    path('verify/<uuid:token>/', views.verify_token, name='verify_token'),
]