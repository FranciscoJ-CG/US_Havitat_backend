# auth_app/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from estate_admin.services import UserStatus
from estate_admin.models import  Relationship, Complex


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        is_admin, related_havitats_ids, related_complexes_ids = UserStatus.is_estate_admin(self.user)
        related_units = []
        if not is_admin:
            related_units = Relationship.objects.filter(user=self.user)
            related_complexes_ids = related_units.values_list('unit__complex', flat=True).distinct()
            related_units = related_units.values('unit__id', 'unit__name', 'unit__complex__id')
        
        related_complexes = Complex.objects.filter(
            id__in=related_complexes_ids).values('id', 'name')

        for related_complex in related_complexes:
            admins = Relationship.objects.filter(
                complex=related_complex['id'], role='estate_admin'
                ).values_list('user_id', flat=True).distinct()
            related_complex['admin_ids'] = list(admins)

        data['user'] = {
            **UserSerializer(self.user).data,
            "is_admin": is_admin,
            "related_complexes": related_complexes,
            "related_units": related_units
        }

        return data 
