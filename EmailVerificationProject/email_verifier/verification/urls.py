from django.urls import path
from . import views # checking

urlpatterns = [
    path('', views.verify_email, name='verify_email'),
    path('verify/<uuid:token>/', views.verify_token, name='verify_token'),
    path('api/status/', views.check_verification_status, name='check_status'),
]