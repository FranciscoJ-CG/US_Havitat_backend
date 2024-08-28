
from rest_framework import serializers
from estate_admin.serializers import UnitSerializer
from .models import AdminFee

class AdminFeeSerializer(serializers.ModelSerializer):
    unit = serializers.SerializerMethodField()
    interest_price = serializers.SerializerMethodField()
    total_to_pay = serializers.SerializerMethodField()
    reduction_deadline = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = AdminFee
        fields = [
            'id',
            'unit',
            'name',
            'amount',
            'billing_period_start',
            'billing_period_end',
            'expiration_date',
            'reduction_deadline',
            'description',
            'late_fee_interest',
            'timestamp',
            'state',
            'interest_price',
            'total_to_pay',
            'paid_interest',
        ]
        read_only_fields = ['id', 'timestamp', 'state']

    def get_unit(self, obj):
        return UnitSerializer(obj.unit).data
    
    def get_interest_price(self, obj):
        return obj.get_interest_price()
    
    def get_total_to_pay(self, obj):
        return obj.get_total_to_pay()
    
