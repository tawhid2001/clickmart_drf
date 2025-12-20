from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

# Create your models here.

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cart of {self.user.username}"
    
    @property
    def subtotal(self):
        subtotal = 0
        for item in self.items.all():
            subtotal += item.product.price * item.quantity
        return subtotal
    
    @property
    def tax_amount(self):
        tax = 0
        for item in self.items.all():
            subtotal = item.product.price * item.quantity
            tax += subtotal * (item.product.tax_percent / 100)
        return tax
    
    @property
    def grand_total(self):
        grand_total = self.subtotal + self.tax_amount
        return grand_total.quantize(Decimal("0.00"))
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} of {self.product.name} in cart of {self.cart.user.username}"
    
    @property
    def total_price(self):
        total_price =  self.product.price * self.quantity
        return total_price