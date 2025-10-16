from django.contrib import admin
from .models import Category, Product, Order, OrderItem, Address, CartItem, Payment

# ----------------------
# Category Admin
# ----------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

# ----------------------
# Product Admin
# ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'price', 'stock']
    list_filter = ['category']

# ----------------------
# Address Admin
# ----------------------
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'street', 'city', 'state', 'pincode', 'country', 'zipcode']
    search_fields = ['user__username', 'city', 'state', 'zipcode']

# ----------------------
# Order Admin
# ----------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'amount']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']

# ----------------------
# OrderItem Admin
# ----------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price']
    search_fields = ['order__id', 'product__name']

# ----------------------
# CartItem Admin
# ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'total_price']
    search_fields = ['user__username', 'product__name']

# ----------------------
# Payment Admin
# ----------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'razorpay_payment_id', 'status', 'amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'razorpay_payment_id', 'razorpay_order_id']
