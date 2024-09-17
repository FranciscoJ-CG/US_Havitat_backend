# documents/serializers.py

from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    file_type = serializers.CharField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'complex', 'file', 'file_type', 'uploaded_at']

    def create(self, validated_data):
        file = validated_data.pop('file')
        validated_data['file_data'] = file.read()
        validated_data['file_type'] = file.content_type
        return super().create(validated_data)

        

