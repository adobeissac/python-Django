from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    """Local record of orders placed via WooCommerce API."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('on-hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    wc_order_id = models.IntegerField(unique=True)
    order_key = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')

    # Billing
    billing_first_name = models.CharField(max_length=100)
    billing_last_name = models.CharField(max_length=100)
    billing_email = models.EmailField()
    billing_address_1 = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postcode = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.wc_order_id} - {self.billing_email}"
