# estate_admin/serializers.py
from rest_framework import serializers

import base64

from .models import (Unit,
                     Complex,
                     ComplexType,
                     UnitType,
                     Relationship,
                     ComplexImage,
                     )
from auth_app.serializers import UserSerializer

class ComplexTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplexType
        fields = ['name']

class ComplexSerializer(serializers.ModelSerializer):
    type = ComplexTypeSerializer()
    
    class Meta:
        model = Complex
        fields = ['id', 'name', 'type', 'havitat']

class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['name']


class RelationshipSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Relationship
        fields = ['user', 'role', 'other_role', 'permission_level']

class UnitSerializer(serializers.ModelSerializer):
    complex = ComplexSerializer()
    type = UnitTypeSerializer()

    class Meta:
        model = Unit
        fields = ['id', 'name', 'comment', 'complex', 'type']

class UnitSerializerWhitRelationship(serializers.ModelSerializer):
    complex = ComplexSerializer()
    type = UnitTypeSerializer()
    relationship_set = RelationshipSerializer(many=True)

    class Meta:
        model = Unit
        fields = ['id', 'name', 'comment', 'complex', 'type',  'relationship_set']
    

class ComplexImageSerializer(serializers.ModelSerializer):
    image_base64 = serializers.SerializerMethodField()

    class Meta:
        model = ComplexImage
        fields = ['complex', 'image_base64']

    def get_image_base64(self, obj):
        if obj.image_data:
            return base64.b64encode(obj.image_data).decode('utf-8')
        return None
