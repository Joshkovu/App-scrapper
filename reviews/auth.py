from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView

from .serializers import SignupSerializer


class EmailTokenSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None or not user.is_active or not user.check_password(attrs.get("password", "")):
            raise serializers.ValidationError("Invalid email or password.")
        refresh = self.get_token(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token), "email": user.email}


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenSerializer


class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = EmailTokenSerializer.get_token(user)
        return Response({"access": str(token.access_token), "refresh": str(token), "email": user.email}, status=status.HTTP_201_CREATED)
