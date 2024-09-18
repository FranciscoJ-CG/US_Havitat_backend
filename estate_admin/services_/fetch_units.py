# estate_admin/services/fetch_units_with_admin_fees.py

from django.shortcuts import get_object_or_404
from estate_admin.serializers import UnitSerializer
from estate_admin.models import Unit 


def fetch_units(complex_id):
    related_units_ids = Unit.objects.filter(complex=complex_id).values_list('id', flat=True)
    related_units = []

    for unit_id in related_units_ids:
        unit_object = get_object_or_404(Unit, id=unit_id)
        unit = UnitSerializer(unit_object).data
        related_units.append(unit)

    return related_units