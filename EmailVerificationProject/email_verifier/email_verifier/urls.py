# email_verifier/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This links the 'api/' prefix to all paths in your app
    path('api/', include('verification.urls')),
    
    # Optional: If you want the root URL to show the email check page
    path('', include('verification.urls')), 
]