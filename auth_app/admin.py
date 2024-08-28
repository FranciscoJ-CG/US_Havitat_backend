# auth_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Q

from .models import UserType, DocumentType, User
from estate_admin.models import Relationship


class CustomUserAdmin(BaseUserAdmin):

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'type', 'document', 'document_type', 'worker')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'type', 'document', 'document_type','worker')}
        ),
    )

    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def _is_super_unit_admin(self, user):
        related_super_units = Relationship.objects.filter(user=user, role='estate_admin').values_list('super_unit', flat=True)
        related_super_units = [unit for unit in related_super_units if unit is not None]
        return bool(related_super_units), related_super_units

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        non_staff_qs = qs.filter(is_staff=False)
        is_super_unit_admin, super_unit_ids = self._is_super_unit_admin(request.user)
        if is_super_unit_admin:
            complex_managers_ids= Relationship.objects.filter(complex__super_unit__in=super_unit_ids, role='estate_admin').values_list('user', flat=True)
            complex_managers_qs= User.objects.filter(id__in=complex_managers_ids)
            combined_qs = qs.filter(Q(id__in=non_staff_qs.values_list('id', flat=True)) | 
                                    Q(id__in=complex_managers_qs.values_list('id', flat=True)))
            return combined_qs

        return non_staff_qs


    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if obj is None:
            return self.add_fieldsets
        non_superuser_fieldsets = (
            (None, {'fields': ('username', 'password', 'worker')}),
            ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'type', 'document', 'document_type')}),
        )
        return non_superuser_fieldsets


    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('username', 'email', 'first_name', 'last_name','worker', 'is_staff')
        return ('username', 'email', 'first_name', 'last_name', 'worker')


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserType)
admin.site.register(DocumentType)