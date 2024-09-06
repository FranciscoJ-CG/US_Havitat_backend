# estate_admin/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from estate_admin.services import UserStatus
from estate_admin.services_.fetch_units_with_admin_fees import fetch_units_with_admin_fees
from estate_admin.models import (Relationship, Unit, Complex, UnitType)
from estate_admin.serializers import (UnitSerializer, ComplexSerializer, UnitSerializerWhitRelationship)
from accounting.models import AdminFee
from accounting.serializers import AdminFeeSerializer
from transactions.services import BaaSConnection, update_transaction_and_admin_fees, fetch_transactions


def update_transaction_statuses(unit_id, complex_id):
    admin_fees = AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])
    transactions = [
        admin_fee.transaction for admin_fee in admin_fees
        if admin_fee.transaction is not None
    ]
    for transaction in transactions:
        status_id = BaaSConnection.get_updated_transaction_status(
            transaction.transfer_id, complex_id)
        update_transaction_and_admin_fees(transaction, status_id)
    
    return AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])


class ComplexInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complex_id):
        try:
            account_data = fetch_transactions(complex_id)
            units = fetch_units_with_admin_fees(complex_id)

            return Response({
                'account_data': account_data,
                'units': units
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            complex = get_object_or_404(Complex, id=unit['complex_id'])
            admin_fees = update_transaction_statuses(unit['id'], complex.id)
            unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
            
            relationship = relationships.get(unit=unit['id'])
            unit['relationship'] = {
                'role': relationship.role, 
                'permission_level': relationship.permission_level
            }

            admin_id = Relationship.objects.filter(complex=complex, role='estate_admin').values_list('user_id', flat=True).first()
            unit['complex'] = {
                'name': complex.name, 
                'id': complex.id, 
                'admin_id': admin_id
            }
            unit['type'] = UnitType.objects.get(id=unit['type_id']).name

        return Response({'units': units})


class UnitDetail(APIView):
    def get(self, request, id):
        unit = get_object_or_404(Unit, id=id)
        serializer = UnitSerializerWhitRelationship(unit)
        data = serializer.data
        admin_fees = AdminFee.objects.filter(unit=id, state='pending')
        data['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data

        return Response(data, status=status.HTTP_200_OK)
