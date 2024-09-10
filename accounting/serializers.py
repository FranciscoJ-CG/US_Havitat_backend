
from rest_framework import serializers
from accounting.models import AdminFee
from estate_admin.models import Unit

class AdminFeeSerializer(serializers.ModelSerializer):
    interest_price = serializers.SerializerMethodField()
    total_to_pay = serializers.SerializerMethodField()
    reduction_deadline = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Unit.objects.all())

    class Meta:
        model = AdminFee
        fields = [
            'id',
            'name',
            'unit',
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

    def get_interest_price(self, obj):
        return obj.get_interest_price()
    
    def get_total_to_pay(self, obj):
        return obj.get_total_to_pay()
    
