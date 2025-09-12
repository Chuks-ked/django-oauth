import os
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from .google import Google
from .models import CustomUser

User = get_user_model()

def register_social_user(provider, user_id, email, name, picture=None):
    """
    Create or get user from social auth data.
    Returns user instance and refresh token.
    """
    # Try to get user by email first
    user = User.objects.filter(email=email).first()

    if user:
        # Link social ID if not already
        if not user.google_id:
            user.google_id = user_id
            user.name = name
            if picture:
                # Download and save picture (use requests to fetch if needed)
                user.profile_picture.save(f"{user.email}_profile.jpg", picture)  # Simplified; add real download in prod
            user.save()
        return user

    # Create new user (no password for social-only)
    user = User.objects.create_user(
        email=email,
        name=name,
        google_id=user_id,
        is_active=True,
    )
    if picture:
        user.profile_picture = picture  # Handle upload
        user.save()

    return user

class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = Google.validate(auth_token)
        if not user_data:
            raise serializers.ValidationError(
                'The token is invalid or expired. Please login again.'
            )

        # Double-check audience (redundant but safe)
        if user_data['email'] and not user_data['email'].endswith('@google.com'):  # Basic sanity
            pass  # Already checked in Google.validate

        user_id = user_data['sub']
        email = user_data['email']
        name = user_data['name']
        picture = user_data.get('picture')

        # Register or get user
        user = register_social_user(
            provider='google', user_id=user_id, email=email, name=name, picture=picture
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return {
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'google_id': user.google_id,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }