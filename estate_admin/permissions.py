from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class PermissionManager:
    @staticmethod
    def assign_estate_admin_permissions(user):
        group, created = Group.objects.get_or_create(name='estate_admin')
        if created:
            PermissionManager._add_estate_admin_permissions_to_group(group)
        user.groups.add(group)

    @staticmethod
    def _add_estate_admin_permissions_to_group(group):
        models = ['dynamicrole', 'relationship']
        for model_name in models:
            content_type = ContentType.objects.get(app_label='estate_admin', model=model_name)
            permissions = Permission.objects.filter(content_type=content_type)
            group.permissions.add(*permissions)

        view_only_models = ['unit']
        for model_name in view_only_models:
            content_type = ContentType.objects.get(app_label='estate_admin', model=model_name)
            permissions = Permission.objects.filter(content_type=content_type, codename__startswith='view_')
            group.permissions.add(*permissions)

        content_type = ContentType.objects.get(app_label='auth_app', model='user')
        permissions = Permission.objects.filter(content_type=content_type)
        group.permissions.add(*permissions)
