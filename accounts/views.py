from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import AuthenticationFailed
from .serializers import GoogleSocialAuthSerializer

class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer
    permission_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not data:
            raise AuthenticationFailed('Invalid authentication credentials.')
        return Response(data, status=status.HTTP_200_OK)
