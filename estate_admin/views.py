# estate_admin/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404

from estate_admin.services_.fetch_units import fetch_units
from estate_admin.models import (Relationship, Unit, Complex, UnitType, ComplexImage)
from estate_admin.serializers import (ComplexSerializer, UnitSerializerWhitRelationship, ComplexImageSerializer)


class ComplexInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complex_id):
        try:
            return Response({
                'units': fetch_units(complex_id),
                'complex': ComplexSerializer(Complex.objects.get(id=complex_id)).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UnitManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        relationships = Relationship.objects.filter(user=user)
        unit_ids = relationships.exclude(unit__isnull=True).values_list('unit', flat=True)
        units = Unit.objects.filter(id__in=unit_ids).values()

        for unit in units:
            complex = get_object_or_404(Complex, id=unit['complex_id'])
            
            relationship = relationships.get(unit=unit['id'])
            unit['relationship'] = {
                'role': relationship.role, 
                'permission_level': relationship.permission_level
            }

            admin_ids = Relationship.objects.filter(complex=complex, role='estate_admin').values_list('user_id', flat=True)
            unit['complex'] = {**ComplexSerializer(complex).data, 'admin_ids': admin_ids} 
            unit['type'] = UnitType.objects.get(id=unit['type_id']).name

        return Response({'units': units})


class UnitDetail(APIView):
    def get(self, request, id):
        unit = get_object_or_404(Unit, id=id)
        serializer = UnitSerializerWhitRelationship(unit)
        data = serializer.data

        return Response(data, status=status.HTTP_200_OK)



class ComplexImageView(APIView):
    def get(self, request, complex_id):
        try:
            complex_image = ComplexImage.objects.get(complex=complex_id)
            serializer = ComplexImageSerializer(complex_image)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ComplexImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
