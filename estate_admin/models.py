# estate_admin/models.py
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from auth_app.models import User

class Havitat(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Havitat"
        verbose_name_plural = "Havitats"

class ComplexType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Complejo"
        verbose_name_plural = "Tipos de Complejos"

class Complex(models.Model):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(ComplexType, on_delete=models.CASCADE)
    havitat = models.ForeignKey(Havitat, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    bank_account = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} -- {self.havitat.name}"

    class Meta:
        verbose_name = "Complejo"
        verbose_name_plural = "Complejos"


class UnitType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Unidad"
        verbose_name_plural = "Tipos de Unidades"

class Unit(models.Model):
    name = models.CharField(max_length=255)
    complex = models.ForeignKey(Complex, on_delete=models.CASCADE)
    type = models.ForeignKey(UnitType, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"
        unique_together = ('complex', 'name')


class DynamicRole(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rol Nuevo"
        verbose_name_plural = "Roles Nuevos"


class Relationship(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('leaser', 'Leaser'),
        ('agent', 'Agent'),
        ('possessor', 'Possessor'),
        ('estate_admin', 'Estate Admin'),
        ('other', 'Other'),
    ]
    PERMISSION_LEVEL_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.CASCADE)
    complex = models.ForeignKey(Complex, null=True, blank=True, on_delete=models.CASCADE)
    havitat = models.ForeignKey(Havitat, null=True, blank=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    other_role = models.ForeignKey(DynamicRole, null=True, blank=True, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_LEVEL_CHOICES)

    def save(self, *args, **kwargs):
        self.validate_relationship_constraints()
        super().save(*args, **kwargs)

    def validate_relationship_constraints(self):
        if [self.unit, self.complex, self.havitat].count(None) != 2:
            raise ValidationError("A relationship must be associated with exactly one of unit, complex, or havitat.")
        
        if self.role == 'estate_admin':
            if self.unit is not None:
                raise ValidationError("An estate_admin cannot be related to a unit.")
            if not self.user.worker:
                raise ValidationError("An estate_admin must be a worker.")
            self.user.is_staff = True
            self.user.save()

        if self.role != 'estate_admin' and self.user.relationship_set.filter(role='estate_admin').exists():
            raise ValidationError("A user with a relationship to a unit cannot have the estate_admin role.")

        if self.role != 'other' and self.other_role is not None:
            self.other_role = None


    class Meta:
        unique_together = ('user', 'unit', 'role' )
        verbose_name = "Relación"
        verbose_name_plural = "Relaciones"
