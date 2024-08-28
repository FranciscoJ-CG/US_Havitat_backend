from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import AdminFee
from .serializers import AdminFeeSerializer
from estate_admin.models import Unit

class AdminFeeListView(generics.ListAPIView):
    serializer_class = AdminFeeSerializer

    def get_queryset(self):
        fee_ids_str = self.request.query_params.get('fee_ids', '')
        
        if not fee_ids_str:
            raise ValidationError("Query parameter 'fee_ids' is required.")
        
        try:
            fee_ids = list(map(int, fee_ids_str.split(',')))
        except ValueError:
            raise ValidationError("Invalid 'fee_ids' format. It should be a comma-separated list of numbers.")

        return AdminFee.objects.filter(id__in=fee_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AdminFeeView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data.get('fee_info')
        if not data['reduction_deadline']:
            del data['reduction_deadline']

        serializer = AdminFeeSerializer(data=data)
        if serializer.is_valid():
            complex_id = request.data.get('complex_id')
            unit_ids = request.data.get('unit_ids', [])
            havitat_id = request.data.get('havitat_id')

            units = []
            if unit_ids:
                units = Unit.objects.filter(id__in=unit_ids)
            elif complex_id:
                units = Unit.objects.filter(complex__id=complex_id)
            elif havitat_id:
                units = Unit.objects.filter(complex__havitat__id=havitat_id)

            if not units:
                return Response({"error": "No units found"}, status=status.HTTP_404_NOT_FOUND)

            fee_info = serializer.validated_data
            try:
                with transaction.atomic():
                    for unit in units:
                        AdminFee.objects.create(
                            unit=unit,
                            name=fee_info['name'],
                            amount=fee_info['amount'],
                            billing_period_start=fee_info['billing_period_start'],
                            billing_period_end=fee_info['billing_period_end'],
                            expiration_date=fee_info.get('expiration_date'),
                            late_fee_interest=fee_info['late_fee_interest'],
                            reduction_deadline=fee_info.get('reduction_deadline'),
                            description=fee_info.get('description', ''),
                        )
                return Response({"success": "Balance modifications created successfully"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(e)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        fee_ids = request.data.get('fee_ids')
        if not fee_ids or not isinstance(fee_ids, list):
            return Response({"error": "A list of fee_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                deleted, _ = AdminFee.objects.filter(id__in=fee_ids).delete()
                if deleted == 0:
                    return Response({"error": "No AdminFee objects found to delete"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"success": f"{deleted} AdminFee objects deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)