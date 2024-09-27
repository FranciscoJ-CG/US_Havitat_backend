# auth_app/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission

import uuid

class UserType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    type = models.ForeignKey(UserType, on_delete=models.PROTECT, null=True)
    document = models.CharField(max_length=15) 
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, null=True)
    worker = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['document', 'document_type'], name='unique_document_per_type')
        ]
    

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

