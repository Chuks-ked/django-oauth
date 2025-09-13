import os
import logging
import requests
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from .google import Google


User = get_user_model()

logger = logging.getLogger(__name__)

def register_social_user(provider, user_id, email, name, picture=None):
    user = User.objects.filter(email=email).first()
    if user and user.google_id and user.google_id != user_id:
        raise ValidationError('This email is linked to a different Google account.')
    if user:
        if not user.google_id:
            user.google_id = user_id
            user.name = name
            if picture:
                try:
                    response = requests.get(picture, timeout=5)
                    response.raise_for_status()
                    user.profile_picture.save(
                        f"{user.email}_profile.jpg", ContentFile(response.content), save=False
                    )
                except requests.RequestException as e:
                    logger.error(f"Failed to download profile picture: {str(e)}")
            user.save()
        return user
    user = User.objects.create_user(
        email=email, name=name, google_id=user_id, is_active=True
    )
    if picture:
        try:
            response = requests.get(picture, timeout=5)
            response.raise_for_status()
            user.profile_picture.save(
                f"{user.email}_profile.jpg", ContentFile(response.content), save=False
            )
        except requests.RequestException as e:
            logger.error(f"Failed to download profile picture: {str(e)}")
    user.save()
    return user

class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = Google.validate(auth_token)
        if not user_data or not user_data.get('email_verified'):
            raise serializers.ValidationError(
                'The token is invalid, expired, or email not verified.'
            )
        user_id = user_data['sub']
        email = user_data['email']
        name = user_data['name']
        picture = user_data.get('picture')
        user = register_social_user(
            provider='google', user_id=user_id, email=email, name=name, picture=picture
        )
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