import os
import logging
import requests
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from .google import Google
from .apple import Apple

User = get_user_model()

logger = logging.getLogger(__name__)

def register_social_user(provider, user_id, email, name=''):
    user = User.objects.filter(email=email).first()
    if user:
        if user.auth_provider != provider:
            raise ValidationError(
                f'This email is registered with {user.auth_provider.capitalize()}. Please log in using {user.auth_provider.capitalize()}.'
            )
        if provider == 'google' and user.google_id and user.google_id != user_id:
            raise ValidationError('This email is linked to a different Google account.')
        if provider == 'apple' and user.apple_id and user.apple_id != user_id:
            raise ValidationError('This email is linked to a different Apple account.')
        if provider == 'google' and not user.google_id:
            user.google_id = user_id
            user.name = name
            user.save()
        if provider == 'apple' and not user.apple_id:
            user.apple_id = user_id
            user.name = name
            user.save()
        return user

    extra_fields = {
        'name': name,
        'auth_provider': provider,
        'is_active': True,
    }
    if provider == 'google':
        extra_fields['google_id'] = user_id
    elif provider == 'apple':
        extra_fields['apple_id'] = user_id
    user = User.objects.create_user(
        email=email,
        **extra_fields
    )
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
        user = register_social_user(
            provider='google', user_id=user_id, email=email, name=name
        )
        refresh = RefreshToken.for_user(user)
        return {
            'userId': user.id,
            'user': {
                'email': user.email,
                'name': user.name,
                'google_id': user.google_id,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

class AppleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()
    full_name = serializers.JSONField(required=False, allow_null=True)

    def validate(self, attrs):
        id_token = attrs['auth_token']
        user_data = Apple.validate(id_token)
        if not user_data or not user_data.get('email_verified'):
            raise serializers.ValidationError(
                'The token is invalid, expired, or email not verified.'
            )
        user_id = user_data['sub']
        email = user_data['email']
        full_name = attrs.get('full_name')
        name = ''
        if full_name:
            first_name = full_name.get('firstName', '')
            last_name = full_name.get('lastName', '')
            name = f"{first_name} {last_name}".strip()
        user = register_social_user(
            provider='apple', user_id=user_id, email=email, name=name
        )
        refresh = RefreshToken.for_user(user)
        return {
            'userId': user.id,
            'user': {
                'email': user.email,
                'name': user.name,
                'apple_id': user.apple_id,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

class TokenResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    data = serializers.DictField(allow_empty=True)
    error = serializers.DictField(allow_null=True)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    email = serializers.EmailField(help_text="User's email address for authentication")
    password = serializers.CharField(write_only=True, help_text="User's password for authentication")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError({"detail": "Both email and password are required."})

        user = User.objects.filter(email=email).first()
        if user and user.auth_provider != 'email':
            raise ValidationError(
                'This account is registered with Google OAuth. Please log in using Google.'
            )

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user or not user.is_active:
            raise serializers.ValidationError({"detail": "Invalid credentials or inactive account."})

        data = super().validate(attrs)
        self.user = user
        data.update({
            'userId': user.id,
            'user': {
                'email': user.email,
                'name': user.name,
            }
        })
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password], help_text="User's password")
    password2 = serializers.CharField(write_only=True, required=True, help_text="Confirm password")

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'location', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Password fields didn't match."})
        if User.objects.filter(email=attrs['email'], auth_provider='google').exists():
            raise ValidationError(
                'This email is registered with Google OAuth. Please log in using Google.'
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                name=validated_data.get('name', ''),
                phone_number=validated_data.get('phone_number', ''),
                location=validated_data.get('location', ''),
                auth_provider='email',
            )
            return user
        except IntegrityError:
            raise ValidationError({"detail": "This email is registered with Google OAuth. Please log in using Google."})