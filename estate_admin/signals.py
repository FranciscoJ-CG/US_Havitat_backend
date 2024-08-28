from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Relationship
from .permissions import PermissionManager

@receiver(post_save, sender=Relationship)
def assign_permissions(sender, instance, created, **kwargs):
    if created and instance.role == 'estate_admin':
        PermissionManager.assign_estate_admin_permissions(instance.user)
