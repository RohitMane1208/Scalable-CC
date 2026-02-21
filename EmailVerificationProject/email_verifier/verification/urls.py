from django.urls import path
from . import views

urlpatterns = [
    path('', views.verify_email, name='verify_email'),
    path('verify/<uuid:token>/', views.verify_token, name='verify_token'),
]