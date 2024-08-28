# transactions/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password


# class Bank(models.Model):
#     name = models.CharField(max_length=255)
#     code = models.CharField(max_length=50)
#     country = models.CharField(max_length=100)

#     def __str__(self):
#         return f"{self.name} ({self.code})"

#     class Meta:
#         verbose_name = "Banco"
#         verbose_name_plural = "Bancos"

# class BankAccount(models.Model):
#     ACCOUNT_TYPES = [
#         ('checking', 'Checking'),
#         ('savings', 'Savings'),
#     ]

#     bank = models.ForeignKey(Bank, on_delete=models.PROTECT)
#     account_number = models.CharField(max_length=255)  # Consider encryption
#     account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
#     owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.bank.name} - {self.account_number[-4:]}"

#     class Meta:
#         verbose_name = "Cuenta Bancaria"
#         verbose_name_plural = "Cuentas Bancarias"

# class PaymentMethod(models.Model):
#     METHOD_TYPES = [
#         ('credit_card', 'Credit Card'),
#         ('bank_transfer', 'Bank Transfer'),
#         ('cash', 'Cash'),
#         ('other', 'Other'),
#     ]

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
#     details = models.JSONField()
#     is_default = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.user.username} - {self.get_method_type_display()}"

#     class Meta:
#         verbose_name = "Método de Pago"
#         verbose_name_plural = "Métodos de Pago"


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
    description = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=20, unique=True)
    pin = models.CharField(max_length=128, default='0000')

    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def __str__(self):
        return f"{self.account_number} - {self.complex}"

