
from estate_admin.models import Relationship

class UserStatus:
    @staticmethod 
    def is_havitat_admin(user):
        return Relationship.objects.filter(
            user=user, role='estate_admin').exclude(havitat=None).values_list('havitat', flat=True)

    @staticmethod
    def is_complex_admin(user):
        return Relationship.objects.filter(
            user=user, role='estate_admin').exclude(complex=None).values_list('complex', flat=True)

    @staticmethod
    def is_estate_admin(user):
        related_havitats_ids = UserStatus.is_havitat_admin(user)
        related_complexes_ids = UserStatus.is_complex_admin(user)
        is_admin = bool(related_havitats_ids) or bool(related_complexes_ids)
        return (is_admin, related_havitats_ids, related_complexes_ids)
