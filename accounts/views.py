from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    GoogleSocialAuthSerializer,
    EmailTokenObtainPairSerializer,
    RegisterSerializer,
    TokenResponseSerializer
)

class APIResponse(Response):
    def __init__(self, data=None, message=None, error=None, status=None):
        response_data = {
            'status': 'success' if status and status < 400 else 'error',
            'message': message or ('Success' if status and status < 400 else 'An error occurred'),
            'data': data or {},
            'error': error,
        }
        super().__init__(data=response_data, status=status)

class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer
    permission_classes = []

    @extend_schema(
        request=GoogleSocialAuthSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Successful Google OAuth login",
                examples=[
                    OpenApiExample(
                        name="SuccessExample",
                        value={
                            "status": "success",
                            "message": "Google login successful",
                            "data": {
                                "userId": 0,
                                "user": {
                                    "email": "string",
                                    "name": "string",
                                    "google_id": "string"
                                },
                                "access": "string",
                                "refresh": "string"
                            },
                            "error": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Invalid or expired token",
                examples=[
                    OpenApiExample(
                        name="ErrorExample",
                        value={
                            "status": "error",
                            "message": "Invalid token",
                            "data": {},
                            "error": {"detail": "string"}
                        }
                    )
                ]
            )
        },
        description="Authenticate user with Google OAuth ID token"
    )
    def post(self, request):
        serializer = GoogleSocialAuthSerializer(data=request.data)
        if serializer.is_valid():
            return APIResponse(
                data=serializer.validated_data,
                message="Google login successful",
                status=status.HTTP_200_OK
            )
        return APIResponse(error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailTokenObtainPairView(TokenObtainPairView):
    permission_classes = []
    serializer_class = EmailTokenObtainPairSerializer

    @extend_schema(
        request=EmailTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Successful login",
                examples=[
                    OpenApiExample(
                        name="SuccessExample",
                        value={
                            "status": "success",
                            "message": "Login successful",
                            "data": {
                                "userId": 0,
                                "user": {
                                    "email": "string",
                                    "name": "string"
                                },
                                "access": "string",
                                "refresh": "string"
                            },
                            "error": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Invalid credentials or missing fields",
                examples=[
                    OpenApiExample(
                        name="ErrorExample",
                        value={
                            "status": "error",
                            "message": "Invalid credentials",
                            "data": {},
                            "error": {"detail": "string"}
                        }
                    )
                ]
            )
        },
        description="Authenticate user with email and password to obtain JWT tokens"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            response_data = super().post(request, *args, **kwargs).data
            response_data['userId'] = serializer.user.id
            response_data['user'] = {
                'email': serializer.user.email,
                'name': serializer.user.name,
            }
            return APIResponse(data=response_data, message="Login successful", status=status.HTTP_200_OK)
        return APIResponse(error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = []

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=TokenResponseSerializer,
                description="User registered successfully",
                examples=[
                    OpenApiExample(
                        name="SuccessExample",
                        value={
                            "status": "success",
                            "message": "User created successfully",
                            "data": {
                                "userId": 0,
                                "user": {
                                    "email": "string",
                                    "name": "string",
                                    "phone_number": "string",
                                    "location": "string"
                                },
                                "access": "string",
                                "refresh": "string"
                            },
                            "error": None
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                response=TokenResponseSerializer,
                description="Validation errors",
                examples=[
                    OpenApiExample(
                        name="ErrorExample",
                        value={
                            "status": "error",
                            "message": "An error occurred",
                            "data": {},
                            "error": {"detail": "string"}
                        }
                    )
                ]
            )
        },
        description="Register a new user with name, email, phone, location, and password"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            data = {
                'userId': user.id,
                'user': {
                    'email': user.email,
                    'name': user.name,
                    'phone_number': user.phone_number,
                    'location': user.location,
                },
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            return APIResponse(
                data=data,
                message="User created successfully",
                status=status.HTTP_201_CREATED
            )
        return APIResponse(error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)