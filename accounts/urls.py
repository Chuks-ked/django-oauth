# accounts/urls.py
from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView  # For refresh endpoint

urlpatterns = [
    path('auth/google/', GoogleSocialAuthView.as_view(), name='google_auth'),
    path('auth/login/', EmailTokenObtainPairView.as_view(), name='login'),
    path('auth/signup/', RegisterView.as_view(), name='signup'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# In project/urls.py: path('api/', include('accounts.urls')),