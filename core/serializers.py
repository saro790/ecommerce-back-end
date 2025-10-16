# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Category, Address, Order, OrderItem, Payment

# ------------------------------
# Category Serializer
# ------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# ------------------------------
# Product Serializer
# ------------------------------
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # Nested serializer

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'image', 'category']

# ------------------------------
# Address Serializer
# ------------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

# ------------------------------
# OrderItem Serializer
# ------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.FloatField(source='product.price', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_name', 'price', 'quantity']

# ------------------------------
# Order Serializer
# ------------------------------
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.FloatField(source='total_price', read_only=True)
    date_ordered = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'date_ordered', 'items', 'total_price']

# ------------------------------
# User Registration Serializer
# ------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

# ------------------------------
# Payment Serializer
# ------------------------------
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("user", "created_at")
