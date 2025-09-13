from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Google:
    @staticmethod
    def validate(auth_token):
        try:
            idinfo = id_token.verify_oauth2_token(
                auth_token, google_requests.Request(), audience=settings.GOOGLE_CLIENT_ID
            )
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"Invalid issuer: {idinfo.get('iss')}")
                return None
            return {
                'sub': idinfo['sub'],
                'email': idinfo.get('email', ''),
                'name': idinfo.get('name', ''),
                'email_verified': idinfo.get('email_verified', False),
            }
        except ValueError as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None