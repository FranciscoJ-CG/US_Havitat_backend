# estate_admin/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import redirect

from auth_app.models import User
from .models import (Havitat,
                     ComplexType,
                     Complex,
                     UnitType,
                     Unit,
                     Relationship,
                     DynamicRole,
                     )
from .forms import  RelationshipForm
from .helpers import UserStatus


def format_currency(value):
    main_part, cents = f"{value:,.2f}".split(".")
    return format_html(
        '{}.<span style="font-size:0.85em;">{}</span>',
        main_part,
        cents
    )


class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'complex', 'type', 'short_comment' )

    def short_comment(self, obj):
        return format_html(
            '<div class="comment" style="cursor: pointer; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" '
            'onclick="toggleComment(this)">{}</div>', obj.comment
        )
    short_comment.short_description = 'Comment'

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Unit.objects.all()
        related_complexes = UserStatus.is_complex_admin(request.user)
        if bool(related_complexes):
            return Unit.objects.filter(complex__in=related_complexes)
        related_havitats = UserStatus.is_havitat_admin(request.user)
        if bool(related_havitats):
            return Unit.objects.filter(complex__havitat__in=related_havitats)

        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        related_complexes = UserStatus.is_complex_admin(request.user)
        if bool(related_complexes) and db_field.name == 'complex':
                kwargs["queryset"] = Complex.objects.filter(id__in=related_complexes)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        if UserStatus.is_complex_admin(request.user):
            return True
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if UserStatus.is_complex_admin(request.user):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if UserStatus.is_complex_admin(request.user):
            return True
        return super().has_delete_permission(request, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not self.has_change_permission(request):
            self.message_user(request, "No tienes permiso para editar este registro.", level='error')
            return redirect('/admin/estate_admin/unit/')
        return super().change_view(request, object_id, form_url, extra_context)


    class Media:
        js = ('admin/js/display_comment.js',)


class RelationshipAdmin(admin.ModelAdmin):
    form = RelationshipForm
    readonly_fields = []

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Relationship.objects.all()
        
        related_havitats = UserStatus.is_havitat_admin(request.user)
        if bool(related_havitats):
            return Relationship.objects.filter(complex__havitat__in=related_havitats)

        related_complexes = UserStatus.is_complex_admin(request.user)
        related_units = Unit.objects.filter(complex__in=related_complexes)
        return Relationship.objects.filter(unit__in=related_units)

    def get_fields(self, request, obj=None):
        fields = ['user', 'role', 'other_role', 'permission_level']
        related_havitats = UserStatus.is_havitat_admin(request.user)
        
        if request.user.is_superuser:
            return fields + ['complex', 'havitat', 'unit']
        elif bool(related_havitats):
            return fields + ['complex']
        else: # user is complex admin
            return fields + ['unit']

    def get_list_display(self, request):
        related_havitats = UserStatus.is_havitat_admin(request.user)
        
        if request.user.is_superuser:
            return ('user', 'unit', 'complex', 'havitat', 'role', 'other_role', 'permission_level')
        elif bool(related_havitats):
            return ('user', 'complex', 'role', 'other_role', 'permission_level')
        else: # user is complex admin
            return ('user', 'unit', 'role', 'other_role', 'permission_level')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            related_havitats = UserStatus.is_havitat_admin(request.user)
            related_complexes = UserStatus.is_complex_admin(request.user)

            if db_field.name == 'unit' and bool(related_complexes):
                kwargs["queryset"] = Unit.objects.filter(complex__in=related_complexes)
            elif db_field.name == 'user':
                if bool(related_havitats):
                    kwargs["queryset"] = User.objects.filter(worker= True, relationship__unit__isnull=True)
                else:
                    kwargs["queryset"] = User.objects.filter(is_staff=False)
            elif db_field.name == 'complex' and bool(related_havitats):
                kwargs["queryset"] = Complex.objects.filter(havitat__in=related_havitats)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        form.is_havitat_admin = UserStatus.is_havitat_admin(request.user)
        return form


class ComplexAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'havitat', 'bank_account')

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Complex.objects.all()
        related_havitats = UserStatus.is_havitat_admin(request.user)
        if bool(related_havitats):
            return Complex.objects.filter(havitat__in=related_havitats)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if  request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'havitat':
            related_havitats = UserStatus.is_havitat_admin(request.user)
            if bool(related_havitats):
                kwargs["queryset"] = Havitat.objects.filter(id__in=related_havitats)
            return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Unit, UnitAdmin)
admin.site.register(Relationship, RelationshipAdmin)
admin.site.register(Complex, ComplexAdmin)
admin.site.register(Havitat)
admin.site.register(ComplexType)
admin.site.register(UnitType)
admin.site.register(DynamicRole)




# class AdminBalanceAdmin(admin.ModelAdmin):
#     form = AdminBalanceForm
#     list_display= ( 'unit', 'formatted_balance', 'get_complex')
#     ordering = ['unit__complex__name']

#     @admin.display(ordering='unit__complex__name', description='Complex')
#     def get_complex(self, obj):
#         return obj.unit.complex.name if obj.unit and obj.unit.complex else 'N/A'
#     get_complex.short_description = 'Complex'

#     def formatted_balance(self, obj):
#         return format_currency(obj.balance)
#     formatted_balance.short_description = 'Balance $'


#     def get_queryset(self, request):
#         related_havitats = UserStatus.is_havitat_admin(request.user)
#         related_complexes = UserStatus.is_complex_admin(request.user)

#         if request.user.is_superuser:
#             return AdminBalance.objects.all()
#         elif bool(related_complexes): # user is complex admin
#             related_units = Unit.objects.filter(complex__in=related_complexes)
#             return AdminBalance.objects.filter(unit__in=related_units)
#         elif bool(related_havitats): # user is super unit admin
#             related_units = Unit.objects.filter(complex__havitat__in=related_havitats)
#             return AdminBalance.objects.filter(unit__in=related_units)

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == 'unit' and not request.user.is_superuser:
#             related_complexes = UserStatus.is_complex_admin(request.user)
#             if bool(related_complexes): # user is complex admin
#                 kwargs["queryset"] = Unit.objects.filter(complex__in=related_complexes)

#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

#     def get_readonly_fields(self, request, obj=None):
#         if obj:
#             return ['unit']
#         return []

#     def has_add_permission(self, request):
#         if UserStatus.is_complex_admin(request.user):
#             return True
#         return super().has_add_permission(request)

#     def has_change_permission(self, request, obj=None):
#         if UserStatus.is_complex_admin(request.user):
#             return True
#         return super().has_change_permission(request, obj)

#     def has_delete_permission(self, request, obj=None):
#         if UserStatus.is_complex_admin(request.user):
#             return True
#         return super().has_delete_permission(request, obj)
    
#     def change_view(self, request, object_id, form_url='', extra_context=None):
#         if not self.has_change_permission(request):
#             self.message_user(request, "No tienes permiso para editar este registro.", level='error')
#             return redirect('/admin/estate_admin/adminbalance/')
#         return super().change_view(request, object_id, form_url, extra_context)

#     def get_form(self, request, obj=None, **kwargs):
#         form = super().get_form(request, obj, **kwargs)
#         form.user = request.user
#         return form

#     class Media:
#         js = ('admin/js/format_monetary_input.js',)
