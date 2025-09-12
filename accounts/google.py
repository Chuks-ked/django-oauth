from google.auth.transport import requests
from google.oauth2 import id_token
from django.conf import settings

class Google:
    """Google class to fetch and validate the user info from ID token."""

    @staticmethod
    def validate(auth_token):
        """
        Validates the Google ID token and returns user info if valid.
        """
        try:
            # Verify token with your client ID (audience)
            idinfo = id_token.verify_oauth2_token(auth_token, requests.Request(), audience=settings.GOOGLE_CLIENT_ID)

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError("Invalid issuer")

            # Extract relevant user data
            return {
                'sub': idinfo['sub'],  # Google user ID
                'email': idinfo.get('email', ''),
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),  # Profile pic URL
            }
        except ValueError as e:
            # Includes invalid/expired token errors
            return None  # Will be handled in serializer