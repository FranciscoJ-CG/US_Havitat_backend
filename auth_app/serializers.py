# auth_app/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from estate_admin.services import UserStatus


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        is_admin, _, _ = UserStatus.is_estate_admin(self.user)

        data.update({  'user':{ **UserSerializer(self.user).data, "is_admin": is_admin} })
        return data
