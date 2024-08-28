# estate_admin/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

import requests, json

from .models import (Relationship,
                     Unit,
                     Complex,
                     UnitType,
)

from .serializers import (
                          UnitSerializer,
                          ComplexSerializer,
                          UnitSerializerWhitRelationship
)
from .helpers import UserStatus
from accounting.models import AdminFee
from accounting.serializers import AdminFeeSerializer
from transactions.views import  coink_login_data   
from transactions.services import BaaSConnection


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_managed_complexes(request):
    user = request.user
    managed_complexes_ids = UserStatus.is_complex_admin(user)

    managed_complexes = Complex.objects.filter(id__in=managed_complexes_ids)
    serializer = ComplexSerializer(managed_complexes, many=True)
    managed_complexes = serializer.data

    data = { 'managed_complexes': managed_complexes }

    return Response(data)

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_related_units(request):
    user = request.user
    relationships = Relationship.objects.filter(user=user)
    unit_ids = relationships.exclude(unit__isnull=True).values_list('unit', flat=True)
    units = Unit.objects.filter(id__in=unit_ids).values()

    for unit in units:
        admin_fees = AdminFee.objects.filter(unit=unit['id'], state__in=['pending', 'processing'])


        transactions = [admin_fee.transaction for admin_fee in admin_fees
                        if admin_fee.transaction is not None
                        and admin_fee.state in ['pending', 'processing']
                        ]
        
        for transaction in transactions:
            status_id = BaaSConnection.get_updated_transaction_status(
                transaction.transfer_id, coink_login_data)
            BaaSConnection.update_transaction_and_admin_fees(transaction, status_id)

        admin_fees = AdminFee.objects.filter(unit=unit['id'], state__in=['pending', 'processing'])

        unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
        relationship = relationships.get(unit=unit['id'])
        unit['relationship'] = {
            'role': relationship.role, 
            'permission_level': relationship.permission_level
        }
        
        complex = Complex.objects.get(id=unit['complex_id'])
        try:
            admin_id = Relationship.objects.get(complex=complex, role='estate_admin').user.id
        except Relationship.DoesNotExist:
            admin_id = None
        unit['complex'] = {
            'name': complex.name, 
            'id': complex.id, 
            'admin_id': admin_id
        }
        
        unit['type'] = UnitType.objects.get(id=unit['type_id']).name

    data = { 'units': units }

    return Response(data)


class ComplexUnits(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, complex_id):
        related_units_ids = Unit.objects.filter(complex=complex_id).values_list('id', flat=True)

        print('related_units_ids', related_units_ids)
        
        related_units = []
        for unit_id in related_units_ids:
            admin_fees = AdminFee.objects.filter(
                Q(unit=unit_id) & (
                    Q(state='pending') | 
                    (Q(state='paid') & Q(transaction__timestamp__gte=timezone.now() - timezone.timedelta(days=30)))
                )
            )
            unit_object = Unit.objects.get(id=unit_id)
            complex = Complex.objects.get(id=unit_object.complex.id)
            unit = UnitSerializer(unit_object).data
            unit['complex'] = {'complex_id': complex.id, 'name':complex.name} 
            unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
            related_units.append(unit)

        return Response(related_units, status=status.HTTP_200_OK)


class UnitDetail(APIView):
    def get(self, request, id):
        unit = Unit.objects.get(id=id)
        serializer = UnitSerializerWhitRelationship(unit)
        data = serializer.data
        admin_fees = AdminFee.objects.filter(unit=id, state='pending')
        serializer = AdminFeeSerializer(admin_fees, many=True)
        data['admin_fees'] = serializer.data


        return Response(data, status=status.HTTP_200_OK)

