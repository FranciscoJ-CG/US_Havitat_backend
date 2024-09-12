# auth_app/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission

class UserType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Usuario"
        verbose_name_plural = "Tipos de Usuarios"

class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"

class User(AbstractUser):
    type = models.ForeignKey(UserType, on_delete=models.PROTECT,  null=True)
    document = models.CharField(max_length=15) 
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, null=True)
    worker = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'document_type'], name='unique_document_per_type')
        ]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    

    groups = models.ManyToManyField(
        Group,
        related_name='auth_app_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='auth_app_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

    def clean(self):
        if not self.document.isdigit():
            raise ValidationError("Document must be numeric")

