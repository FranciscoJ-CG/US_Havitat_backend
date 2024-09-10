# estate_admin/services/fetch_units_with_admin_fees.py

from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from accounting.models import AdminFee
from accounting.serializers import AdminFeeSerializer
from estate_admin.serializers import UnitSerializer
from estate_admin.models import Unit 


def fetch_units_with_last_admin_fees(complex_id):
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
        unit = UnitSerializer(unit_object).data
        unit['admin_fees'] = AdminFeeSerializer(admin_fees, many=True).data
        related_units.append(unit)

    return related_units