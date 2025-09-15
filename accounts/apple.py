import jwt
from jwt.algorithms import RSAAlgorithm
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

APPLE_JWKS_URL = 'https://appleid.apple.com/auth/keys'


class Apple:
    @staticmethod
    def get_public_key(kid):
        try:
            jwks = requests.get(APPLE_JWKS_URL).json()['keys']
            for key in jwks:
                if key['kid'] == kid:
                    return RSAAlgorithm.from_jwk(key)
            return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Apple JWKS: {str(e)}")
            return None

    @staticmethod
    def validate(id_token):
        try:
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            alg = header.get('alg')

            public_key = Apple.get_public_key(kid)
            if not public_key:
                raise ValueError("Invalid key ID")

            decoded = jwt.decode(
                id_token,
                public_key,
                algorithms=[alg],
                audience=settings.APPLE_BUNDLE_ID,
                issuer='https://appleid.apple.com',
                options={"require": ["exp", "iss", "aud"]},
            )
            return {
                'sub': decoded['sub'],
                'email': decoded.get('email', ''),
                'email_verified': decoded.get('email_verified', False),
            }
        except jwt.ExpiredSignatureError:
            logger.error("Apple ID token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid Apple ID token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Apple validation error: {str(e)}")
            return None