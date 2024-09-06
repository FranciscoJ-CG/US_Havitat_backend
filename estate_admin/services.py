
from estate_admin.models import Relationship 

class UserStatus:
    @staticmethod 
    def is_havitat_admin(user):
        related_havitats_ids = Relationship.objects.filter(user=user, role='estate_admin').values_list('havitat', flat=True)
        return [unit for unit in related_havitats_ids if unit is not None]

    @staticmethod
    def is_complex_admin(user):
        related_complexes_ids = Relationship.objects.filter(user=user, role='estate_admin').values_list('complex', flat=True)
        return [complex for complex in related_complexes_ids if complex is not None]

    @staticmethod
    def is_estate_admin(user):
        related_havitats_ids = UserStatus.is_havitat_admin(user)
        related_complexes_ids = UserStatus.is_complex_admin(user)
        is_admin = bool(related_havitats_ids) or bool(related_complexes_ids)
        return (is_admin, related_havitats_ids, related_complexes_ids)
