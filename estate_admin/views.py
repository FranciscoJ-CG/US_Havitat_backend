# estate_admin/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
# from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

# from estate_admin.services import UserStatus
from estate_admin.services_.fetch_units import fetch_units
from estate_admin.models import (Relationship, Unit, Complex, UnitType)
from estate_admin.serializers import (ComplexSerializer, UnitSerializerWhitRelationship)
# from accounting.models import AdminFee
# from accounting.serializers import AdminFeeSerializer
# from transactions.services import BaaSConnection, update_transaction_and_admin_fees, fetch_transactions


# def update_transaction_statuses(unit_id, complex_id):
#     admin_fees = AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])
#     transactions = [
#         admin_fee.transaction for admin_fee in admin_fees
#         if admin_fee.transaction is not None
#     ]
#     for transaction in transactions:
#         status_id = BaaSConnection.get_updated_transaction_status(
#             transaction.transfer_id, complex_id)
#         update_transaction_and_admin_fees(transaction, status_id)
    
#     return AdminFee.objects.filter(unit=unit_id, state__in=['pending', 'processing'])


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
            # admin_fees = update_transaction_statuses(unit['id'], complex.id)
            # unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
            
            relationship = relationships.get(unit=unit['id'])
            unit['relationship'] = {
                'role': relationship.role, 
                'permission_level': relationship.permission_level
            }

            admin_id = Relationship.objects.filter(complex=complex, role='estate_admin').values_list('user_id', flat=True).first()
            unit['complex'] = {**ComplexSerializer(complex).data, 'admin_id': admin_id} 
            unit['type'] = UnitType.objects.get(id=unit['type_id']).name

        return Response({'units': units})


class UnitDetail(APIView):
    def get(self, request, id):
        unit = get_object_or_404(Unit, id=id)
        serializer = UnitSerializerWhitRelationship(unit)
        data = serializer.data
        # admin_fees = AdminFee.objects.filter(unit=id, state='pending')
        # data['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data

        return Response(data, status=status.HTTP_200_OK)
