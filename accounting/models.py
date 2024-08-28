from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from decimal import Decimal, ROUND_HALF_UP

class AdminFee(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
    ]

    name = models.CharField(max_length=50)
    unit = models.ForeignKey('estate_admin.Unit', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    late_fee_interest = models.DecimalField(max_digits=5, decimal_places=2)
    reduction_deadline = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    transaction = models.ForeignKey('transactions.Transaction', on_delete=models.SET_NULL, null=True, blank=True)
    paid_interest = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        month_name = self.billing_period_start.strftime("%B")
        return f"{self.name} - {self.unit} - {month_name}"
    
    def save(self, *args, **kwargs):
        if self.reduction_deadline and self.expiration_date:
            if self.reduction_deadline >= self.expiration_date:  
                raise ValidationError({
                    'reduction_deadline': "The reduction deadline must be earlier than the expiration date."
                    }) 
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Cobro"
        verbose_name_plural = "Cobros"

    def calculate_late_interest(self, date):
        days_late = (date - self.expiration_date).days
        monthly_interest = Decimal(self.late_fee_interest) / Decimal('100')
        interest = self.amount * ((Decimal('1.0') + monthly_interest) ** (Decimal(days_late) / Decimal('30')) - Decimal('1.0'))
        return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_reduction(self, date):
        days_before_deadline = (self.reduction_deadline - date).days
        monthly_interest = Decimal(self.late_fee_interest) / Decimal('100')
        reduction = self.amount * ((Decimal('1.0') + monthly_interest) ** (Decimal(days_before_deadline) / Decimal('30')) - Decimal('1.0'))
        return (-reduction).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_interest_price(self, date=None):
        if self.state == 'paid':
            return self.paid_interest 

        if date is None:
            date = timezone.now().date()
            
        price_variation = Decimal(0.00)
        if self.expiration_date and date > self.expiration_date:
            price_variation = self.calculate_late_interest(date)
        if self.reduction_deadline and date < self.reduction_deadline:
            price_variation = self.calculate_reduction(date)

        return price_variation 
    
    def get_total_to_pay(self, date=None):
        if self.state == 'paid':
            return Decimal(0.00) 
        total = self.amount + self.get_interest_price(date)
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        

