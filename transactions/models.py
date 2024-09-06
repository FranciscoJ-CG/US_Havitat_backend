# transactions/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    transfer_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user} - {self.amount}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"


class TransactionLog(models.Model):
    LOG_TYPES = [
        ('info', 'Info'),
        ('error', 'Error'),
        ('warning', 'Warning'),
    ]

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    log_type = models.CharField(max_length=10, choices=LOG_TYPES)

    def __str__(self):
        return f"{self.transaction} - {self.get_log_type_display()} - {self.timestamp}"

    class Meta:
        verbose_name = "Logs de Transacción"
        verbose_name_plural = "Logs de Transacciones"


class AccountInfo(models.Model):
    complex = models.ForeignKey('estate_admin.Complex', on_delete=models.CASCADE)
    account_id = models.UUIDField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    account_number = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    pin = models.CharField(max_length=128, default='0000')

    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def __str__(self):
        return f"{self.account_number} - {self.complex}"
    
    class Meta:
        verbose_name = "Info de Cuenta"
        verbose_name_plural = "Info de Cuentas"

