from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_page, name='booking'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/check-typo/', views.api_check_typo, name='check_typo'),
    # This matches the link your API will send: http://.../verify/<uuid>/
    path('verify/<uuid:token>/', views.verify_ticket_token, name='verify_ticket'),
]