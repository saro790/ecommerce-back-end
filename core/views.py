# core/views.py
from rest_framework import viewsets, generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Product, Category, Order, OrderItem, Payment
from .serializers import (
    ProductSerializer, CategorySerializer, OrderSerializer,
    OrderItemSerializer, RegisterSerializer, PaymentSerializer
)
import razorpay, hmac, hashlib, json, logging

logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ------------------------------
# Products & Categories
# ------------------------------
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ------------------------------
# User Registration API
# ------------------------------
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not username or not password or not confirm_password:
            return Response({"error": "All fields are required"}, status=400)
        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        User.objects.create_user(username=username, password=password)
        return Response({"message": "User created successfully"}, status=201)


# ------------------------------
# Cart API
# ------------------------------
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user, order__status="Created")


# ------------------------------
# Order History API
# ------------------------------
class OrderHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


# ------------------------------
# Payments API
# ------------------------------
class PaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def record_payment(request):
    data = request.data
    required = ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "amount")
    for k in required:
        if k not in data:
            return Response({"detail": f"Missing {k}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        params_dict = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        verified = True
    except:
        verified = False

    payment = Payment.objects.create(
        user=request.user,
        razorpay_order_id=data["razorpay_order_id"],
        razorpay_payment_id=data["razorpay_payment_id"],
        razorpay_signature=data["razorpay_signature"],
        amount=data["amount"],
        status="paid" if verified else "failed",
        raw_response=data
    )
    serializer = PaymentSerializer(payment)
    return Response(serializer.data, status=status.HTTP_201_CREATED if verified else status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST"])
def razorpay_webhook(request):
    payload = request.body
    signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
    try:
        razorpay_client.utility.verify_webhook_signature(payload, signature, settings.RAZORPAY_WEBHOOK_SECRET)
        return Response({"status": "ok"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# ------------------------------
# Create Order
# ------------------------------
@csrf_exempt
def create_order(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        data = json.loads(request.body)
        amount = int(data.get("amount", 0))
        currency = data.get("currency", "INR")
        address = data.get("address", "")
        cart = data.get("cart", [])

        if amount <= 0:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        razorpay_order = razorpay_client.order.create({
            "amount": amount,
            "currency": currency,
            "payment_capture": 1
        })

        order = Order.objects.create(
            user=request.user,
            razorpay_order_id=razorpay_order["id"],
            amount=amount,
            address=address,
            cart_data=cart,
            status="Created"
        )

        return JsonResponse({
            "razorpay_order_id": razorpay_order["id"],
            "amount": amount,
            "currency": currency,
            "order_id": order.id
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ------------------------------
# Verify Payment
# ------------------------------
@csrf_exempt
def verify_payment(request):
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        order_id = data.get("order_id")

        order = Order.objects.get(id=order_id)

        # Verify signature
        body = razorpay_order_id + "|" + razorpay_payment_id
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            return JsonResponse({"error": "Signature verification failed"}, status=400)

        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.status = "Paid"
        order.save()

        return JsonResponse({
            "success": True,
            "order": {
                "id": order.id,
                "amount": order.amount,
                "status": order.status,
                "razorpay_order_id": order.razorpay_order_id,
                "razorpay_payment_id": order.razorpay_payment_id,
                "created_at": order.created_at
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ------------------------------
# User Orders List
# ------------------------------
@csrf_exempt
def order_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=403)

    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    data = [
        {
            "id": o.id,
            "amount": o.amount,
            "status": o.status,
            "razorpay_order_id": o.razorpay_order_id,
            "razorpay_payment_id": o.razorpay_payment_id,
            "address": o.address,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "cart_data": o.cart_data,
        }
        for o in orders
    ]
    return JsonResponse({"orders": data})
