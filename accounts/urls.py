# accounts/urls.py
from django.urls import path
from .views import GoogleSocialAuthView
from rest_framework_simplejwt.views import TokenRefreshView  # For refresh endpoint

urlpatterns = [
    path('auth/google/', GoogleSocialAuthView.as_view(), name='google_auth'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Mobile can POST {"refresh": "..."} here
]

# In project/urls.py: path('api/', include('accounts.urls')),