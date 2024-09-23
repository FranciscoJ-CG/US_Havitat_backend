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
                     ComplexImage,
                     )
from .forms import  RelationshipForm, ComplexImageForm
from .services import UserStatus


def format_currency(value):
    main_part, cents = f"{value:,.2f}".split(".")
    return format_html(
        '{}.<span style="font-size:0.85em;">{}</span>',
        main_part,
        cents
    )

def get_related_queryset(request, model_class, filter_by):
    if request.user.is_superuser:
        return model_class.objects.all()
    
    related_havitats = UserStatus.is_havitat_admin(request.user)
    if bool(related_havitats):
        return model_class.objects.filter(**{filter_by: related_havitats})

    related_complexes = UserStatus.is_complex_admin(request.user)
    if bool(related_complexes):
        return model_class.objects.filter(complex__in=related_complexes)
    
    return model_class.objects.none()

class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'complex', 'type', 'short_comment' )

    def short_comment(self, obj):
        return format_html(
            '<div class="comment" style="cursor: pointer; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" '
            'onclick="toggleComment(this)">{}</div>', obj.comment
        )
    short_comment.short_description = 'Comment'

    def get_queryset(self, request):
        return get_related_queryset(request, Unit, 'complex__havitat__in')

        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'complex':
            related_complexes = UserStatus.is_complex_admin(request.user)
            if bool(related_complexes):
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
        return get_related_queryset(request, Relationship, 'complex__havitat__in')

    def get_fields(self, request, obj=None):
        base_fields = ['user', 'role', 'other_role', 'permission_level']
        
        if request.user.is_superuser:
            return base_fields + ['complex', 'havitat', 'unit']
        elif UserStatus.is_havitat_admin(request.user):
            return base_fields + ['complex']
        else:  # user is complex admin
            return base_fields + ['unit']

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('user', 'unit', 'complex', 'havitat', 'role', 'other_role', 'permission_level')
        elif bool(UserStatus.is_havitat_admin(request.user)):
            return ('user', 'complex', 'role', 'other_role', 'permission_level')
        else:  # user is complex admin
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
    list_display = ('name', 'type', 'havitat')

    def get_queryset(self, request):
        return get_related_queryset(request, Complex, 'havitat__in')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'havitat' and not request.user.is_superuser:
            related_havitats = UserStatus.is_havitat_admin(request.user)
            if bool(related_havitats):
                kwargs["queryset"] = Havitat.objects.filter(id__in=related_havitats)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



class ComplexImageAdmin(admin.ModelAdmin):
    form = ComplexImageForm
    list_display = ['complex', 'id']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image_data:
            from django.utils.html import mark_safe
            import base64
            encoded = base64.b64encode(obj.image_data).decode()
            return mark_safe(f'<img src="data:image/png;base64,{encoded}" width="200" />')
        return "No Image"

    image_preview.short_description = "Image Preview"

admin.site.register(Unit, UnitAdmin)
admin.site.register(Relationship, RelationshipAdmin)
admin.site.register(Complex, ComplexAdmin)
admin.site.register(Havitat)
admin.site.register(ComplexType)
admin.site.register(UnitType)
admin.site.register(DynamicRole)
admin.site.register(ComplexImage, ComplexImageAdmin)