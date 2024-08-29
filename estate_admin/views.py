# estate_admin/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import (Relationship, Unit, Complex, UnitType)
from .serializers import (UnitSerializer, ComplexSerializer, UnitSerializerWhitRelationship)
from .services import UserStatus
from accounting.models import AdminFee
from accounting.serializers import AdminFeeSerializer
from transactions.views import coink_login_data   
from transactions.services import BaaSConnection


def update_transaction_statuses(unit_id):
    admin_fees = AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])
    transactions = [
        admin_fee.transaction for admin_fee in admin_fees
        if admin_fee.transaction is not None
    ]
    for transaction in transactions:
        status_id = BaaSConnection.get_updated_transaction_status(
            transaction.transfer_id, coink_login_data)
        BaaSConnection.update_transaction_and_admin_fees(transaction, status_id)
    
    return AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])


class ComplexManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        managed_complexes_ids = UserStatus.is_complex_admin(user)
        managed_complexes = Complex.objects.filter(id__in=managed_complexes_ids)
        serializer = ComplexSerializer(managed_complexes, many=True)
        return Response({'managed_complexes': serializer.data})


class UnitManagement(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        relationships = Relationship.objects.filter(user=user)
        unit_ids = relationships.exclude(unit__isnull=True).values_list('unit', flat=True)
        units = Unit.objects.filter(id__in=unit_ids).values()

        for unit in units:
            admin_fees = update_transaction_statuses(unit['id'])
            unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
            
            relationship = relationships.get(unit=unit['id'])
            unit['relationship'] = {
                'role': relationship.role, 
                'permission_level': relationship.permission_level
            }

            complex = get_object_or_404(Complex, id=unit['complex_id'])
            admin_id = Relationship.objects.filter(complex=complex, role='estate_admin').values_list('user_id', flat=True).first()
            unit['complex'] = {
                'name': complex.name, 
                'id': complex.id, 
                'admin_id': admin_id
            }
            unit['type'] = UnitType.objects.get(id=unit['type_id']).name

        return Response({'units': units})


class ComplexUnits(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complex_id):
        related_units_ids = Unit.objects.filter(complex=complex_id).values_list('id', flat=True)
        related_units = []

        for unit_id in related_units_ids:
            admin_fees = AdminFee.objects.filter(
                Q(unit=unit_id) & (
                    Q(state='pending') | 
                    (Q(state='paid') & Q(transaction__timestamp__gte=timezone.now() - timezone.timedelta(days=30)))
                )
            )
            unit_object = get_object_or_404(Unit, id=unit_id)
            complex = unit_object.complex
            unit = UnitSerializer(unit_object).data
            unit['complex'] = {'complex_id': complex.id, 'name': complex.name}
            unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
            related_units.append(unit)

        return Response(related_units, status=status.HTTP_200_OK)


class UnitDetail(APIView):
    def get(self, request, id):
        unit = get_object_or_404(Unit, id=id)
        serializer = UnitSerializerWhitRelationship(unit)
        data = serializer.data
        admin_fees = AdminFee.objects.filter(unit=id, state='pending')
        data['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data

        return Response(data, status=status.HTTP_200_OK)
