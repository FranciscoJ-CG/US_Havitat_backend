# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction
from accounting.models import AdminFee 
from accounting.serializers import AdminFeeSerializer


class TransactionSerializer(serializers.ModelSerializer):
    admin_fees = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'status', 'amount', 'timestamp', 'description', 'transfer_id', 'admin_fees']

    def get_admin_fees(self, obj):
        try:
            admin_fees = AdminFee.objects.filter(transaction=obj)
            return AdminFeeSerializer(admin_fees, many=True).data
        except AdminFee.DoesNotExist:
            return None

class UserInfoSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='phone', read_only=True, allow_blank=True)

class ExternalAccountSerializer(serializers.Serializer):
    bank_id = serializers.IntegerField()

class PSETransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subject = serializers.CharField(max_length=255, default='')
    external_account = ExternalAccountSerializer()
    admin_fee_ids = serializers.ListField(child=serializers.IntegerField())
