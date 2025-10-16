# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# ------------------------------
# Category Model
# ------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# ------------------------------
# Product Model
# ------------------------------
class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

# ------------------------------
# Order Model
# ------------------------------
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default="Created")  # Created, Paid, Failed
    address = models.TextField(blank=True, null=True)
    cart_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

    @property
    def total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())

# ------------------------------
# OrderItem Model
# ------------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def product_name(self):
        return self.product.name

    @property
    def price(self):
        return self.product.price

# ------------------------------
# Address Model
# ------------------------------
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="India")
    zipcode = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}"

# ------------------------------
# CartItem Model
# ------------------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity  # auto calculate total
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

# ------------------------------
# Payment Model
# ------------------------------
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=512, blank=True, null=True)
    amount = models.IntegerField(help_text="Amount in paise")  # store smallest unit
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=50, default="created")  # created / paid / failed / refunded
    method = models.CharField(max_length=50, blank=True, null=True)
    captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.razorpay_payment_id or self.razorpay_order_id} - {self.status}"
