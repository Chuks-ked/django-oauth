# Social Login Backend for Mobile App

This Django REST Framework (DRF) project provides a backend for a mobile app with support for Google OAuth, Apple OAuth, and email/password authentication. It enforces **account exclusivity** (users can only use one authentication method per email) and returns JWT tokens for secure API access. The backend is designed to be production-ready with HTTPS, logging, and CORS support.

## Features
- **Google OAuth**: Sign up or log in using Google ID tokens.
- **Apple OAuth**: Sign up or log in using Apple ID tokens.
- **Email/Password**: Sign up or log in with email and password.
- **Account Exclusivity**: Users registered with one method (e.g., Google) cannot use another (e.g., email/password) with the same email.
- **JWT Authentication**: Returns `access` and `refresh` tokens for secure API calls.
- **Mobile-Friendly**: Supports CORS for mobile app integration.
- **OpenAPI Documentation**: Generated via `drf-spectacular` for API clarity.

## Prerequisites
- Python 3.8+
- Django 4.2+
- PostgreSQL (recommended for production; SQLite for development)
- Google Cloud Console project with OAuth 2.0 Web Client ID
- Apple Developer account with Sign in with Apple enabled
- Git

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Chuks-ked/django-oauth.git
   cd backend
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt drf-spectacular python-decouple pyjwt cryptography requests django-cors-headers
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-django-secret-key
   GOOGLE_CLIENT_ID=your-web-client-id.apps.googleusercontent.com
   APPLE_BUNDLE_ID=com.yourcompany.yourapp
   ```
   - Generate `SECRET_KEY` securely.
   - Get `GOOGLE_CLIENT_ID` from Google Cloud Console (Web Client ID).
   - Get `APPLE_BUNDLE_ID` from Apple Developer Portal (your mobile app’s bundle ID).

5. **Apply Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```

## Project Structure
- `backend/`: Django project directory.
- `accounts/`: App containing authentication logic.
  - `models.py`: Custom user model with `auth_provider`, `google_id`, `apple_id`.
  - `google.py`: Google OAuth token validation.
  - `apple.py`: Apple OAuth token validation.
  - `serializers.py`: Serializers for Google, Apple, and email/password auth.
  - `views.py`: API views for authentication.
  - `urls.py`: API endpoint routes.

## Configuration

### settings.py
Key settings in `backend/settings.py`:
```python
INSTALLED_APPS = [
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'accounts',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
APPLE_BUNDLE_ID = config('APPLE_BUNDLE_ID')
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'capacitor://localhost',
    'http://localhost',
    # Add production URLs
]
CORS_ALLOW_CREDENTIALS = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {'level': 'ERROR', 'class': 'logging.FileHandler', 'filename': 'debug.log'},
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler'},
    },
    'loggers': {'': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True}},
}
```

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a project and enable the Google+ API.
3. Create OAuth 2.0 credentials (Web Client ID).
4. Set authorized redirect URIs (e.g., `http://localhost:8000/api/auth/google/` for dev).
5. Copy the Web Client ID to `.env` as `GOOGLE_CLIENT_ID`.

### Apple OAuth Setup
1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list).
2. Create an App ID with Sign in with Apple enabled.
3. Note your app’s bundle ID (e.g., `com.yourcompany.yourapp`).
4. Add to `.env` as `APPLE_BUNDLE_ID`.

## API Endpoints
All endpoints return a consistent response format:
```json
{
    "status": "success" | "error",
    "message": "string",
    "data": {},
    "error": null | {"detail": "string"}
}
```

### 1. Google OAuth Login
- **URL**: `/api/auth/google/`
- **Method**: POST
- **Body**:
  ```json
  {"auth_token": "<google_id_token>"}
  ```
- **Response (200)**:
  ```json
  {
      "status": "success",
      "message": "Google login successful",
      "data": {
          "userId": 1,
          "user": {"email": "user@example.com", "name": "John Doe", "google_id": "123456"},
          "access": "<jwt_access_token>",
          "refresh": "<jwt_refresh_token>"
      },
      "error": null
  }
  ```
- **Errors** (400):
  - Invalid/expired token: `{"error": {"detail": "The token is invalid, expired, or email not verified."}}`
  - Email tied to email/password: `{"error": {"detail": "This email is registered with email/password. Please log in using your email and password."}}`

### 2. Apple OAuth Login
- **URL**: `/api/auth/apple/`
- **Method**: POST
- **Body**:
  ```json
  {
      "auth_token": "<apple_id_token>",
      "full_name": {"firstName": "John", "lastName": "Doe"}  // Optional, sent on first sign-in
  }
  ```
- **Response (200)**:
  ```json
  {
      "status": "success",
      "message": "Apple login successful",
      "data": {
          "userId": 2,
          "user": {"email": "user@privaterelay.appleid.com", "name": "John Doe", "apple_id": "001234"},
          "access": "<jwt_access_token>",
          "refresh": "<jwt_refresh_token>"
      },
      "error": null
  }
  ```
- **Errors** (400): Similar to Google OAuth.

### 3. Email/Password Signup
- **URL**: `/api/auth/signup/`
- **Method**: POST
- **Body**:
  ```json
  {
      "email": "user@example.com",
      "password": "password123",
      "password2": "password123",
      "name": "John Doe",
      "phone_number": "1234567890",
      "location": "New York"
  }
  ```
- **Response (201)**:
  ```json
  {
      "status": "success",
      "message": "User created successfully",
      "data": {
          "userId": 3,
          "user": {"email": "user@example.com", "name": "John Doe", "phone_number": "1234567890", "location": "New York"},
          "access": "<jwt_access_token>",
          "refresh": "<jwt_refresh_token>"
      },
      "error": null
  }
  ```
- **Errors** (400):
  - Email tied to Google/Apple: `{"error": {"detail": "This email is registered with Google. Please log in using Google."}}`
  - Password mismatch: `{"error": {"password2": "Password fields didn't match."}}`

### 4. Email/Password Login
- **URL**: `/api/auth/login/`
- **Method**: POST
- **Body**:
  ```json
  {"email": "user@example.com", "password": "password123"}
  ```
- **Response (200)**:
  ```json
  {
      "status": "success",
      "message": "Login successful",
      "data": {
          "userId": 3,
          "user": {"email": "user@example.com", "name": "John Doe"},
          "access": "<jwt_access_token>",
          "refresh": "<jwt_refresh_token>"
      },
      "error": null
  }
  ```
- **Errors** (400):
  - Invalid credentials: `{"error": {"detail": "Invalid credentials or inactive account."}}`
  - Email tied to Google/Apple: `{"error": {"detail": "This account is registered with Google. Please log in using Google."}}`

### 5. Token Refresh
- **URL**: `/api/auth/refresh/`
- **Method**: POST
- **Body**:
  ```json
  {"refresh": "<jwt_refresh_token>"}
  ```
- **Response (200)**:
  ```json
  {
      "access": "<new_jwt_access_token>",
      "refresh": "<new_jwt_refresh_token>"  // If ROTATE_REFRESH_TOKENS is True
  }
  ```

## Mobile App Integration
1. **Google OAuth**:
   - Use Google Sign-In SDK to get `idToken`.
   - POST to `/api/auth/google/` with `{"auth_token": "<idToken>"}`.
2. **Apple OAuth**:
   - Use Sign in with Apple SDK to get `idToken` and optional `fullName`.
   - POST to `/api/auth/apple/` with `{"auth_token": "<idToken>", "full_name": {"firstName": "...", "lastName": "..."}}`.
3. **Email/Password**:
   - POST to `/api/auth/signup/` for new users.
   - POST to `/api/auth/login/` for existing users.
4. **Token Handling**:
   - Store `access` and `refresh` tokens securely (e.g., Keychain on iOS, EncryptedSharedPreferences on Android).
   - Use `access` token in `Authorization: Bearer <access_token>` for protected APIs.
   - Refresh tokens via `/api/auth/refresh/` when `access` expires (401 errors).
5. **Error Handling**:
   - Parse `error.detail` for user-friendly messages (e.g., “Please log in using Google”).

## Testing
1. **Google OAuth**:
   - Use [Google OAuth Playground](https://developers.google.com/oauthplayground) to get an ID token.
   - Test: `curl -X POST http://localhost:8000/api/auth/google/ -H "Content-Type: application/json" -d '{"auth_token": "<id_token>"}'`
2. **Apple OAuth**:
   - Use a simulator or real device to get an Apple ID token.
   - Test: `curl -X POST http://localhost:8000/api/auth/apple/ -H "Content-Type: application/json" -d '{"auth_token": "<id_token>", "full_name": {"firstName": "John", "lastName": "Doe"}}'`
3. **Email/Password**:
   - Test signup: `curl -X POST http://localhost:8000/api/auth/signup/ -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123", "password2": "password123", "name": "Test User"}'`
   - Test login: `curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password123"}'`
4. **Exclusivity**:
   - Create a Google user, then try signing up with the same email (should fail).
   - Create an email user, then try Google/Apple login with the same email (should fail).
5. **Unit Tests**:
   ```python
   # accounts/tests.py
   from rest_framework.test import APITestCase
   from rest_framework import status
   from .models import CustomUser

   class AuthTests(APITestCase):
       def test_google_exclusivity(self):
           user = CustomUser.objects.create_user(
               email='test@example.com', google_id='123', auth_provider='google'
           )
           response = self.client.post('/api/auth/signup/', {
               'email': 'test@example.com',
               'password': 'password123',
               'password2': 'password123',
               'name': 'Test User'
           }, format='json')
           self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
           self.assertIn('detail', response.data['error'])

       def test_apple_exclusivity(self):
           user = CustomUser.objects.create_user(
               email='test@example.com', apple_id='001234', auth_provider='apple'
           )
           response = self.client.post('/api/auth/login/', {
               'email': 'test@example.com',
               'password': 'password123'
           }, format='json')
           self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
           self.assertIn('detail', response.data['error'])
   ```
   Run: `python manage.py test`

## Production Deployment
1. **HTTPS**: Use Nginx or a cloud provider (e.g., AWS ALB) with an SSL certificate (e.g., Let’s Encrypt).
2. **Database**: Use PostgreSQL instead of SQLite.
3. **Environment Variables**: Ensure `.env` is not in source control (add to `.gitignore`).
4. **Monitoring**: Check `debug.log` for errors.
5. **Performance**: Cache Apple JWKS (e.g., with `django-cache`) to reduce HTTP calls.
6. **Security**:
   - Validate `GOOGLE_CLIENT_ID` and `APPLE_BUNDLE_ID` match your app’s credentials.
   - Handle Apple’s private/relay emails as unique identifiers.

## Troubleshooting
- **Token Errors**: Check logs (`debug.log`) for validation issues. Ensure `GOOGLE_CLIENT_ID` and `APPLE_BUNDLE_ID` are correct.
- **CORS Issues**: Add mobile app origins to `CORS_ALLOWED_ORIGINS`.
- **Exclusivity Errors**: Verify `auth_provider` is set correctly in the database.
- Contact support or check logs for detailed errors.

## License
MIT License.