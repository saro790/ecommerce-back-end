from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView,
    ProductViewSet,
    CategoryViewSet,
    CartItemViewSet,
    OrderHistoryView,
    PaymentListView,
    record_payment,
    razorpay_webhook,
    create_order,
    verify_payment,
)

# ------------------------------
# Router for ViewSets
# ------------------------------
router = DefaultRouter()
router.register('products', ProductViewSet, basename='products')
router.register('categories', CategoryViewSet, basename='categories')
router.register('cart', CartItemViewSet, basename='cart')

# ------------------------------
# URL Patterns
# ------------------------------
urlpatterns = [
    # ViewSets (Products, Categories, Cart)
    path('', include(router.urls)),

    # User Registration & JWT
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Order History
    path('orders/history/', OrderHistoryView.as_view(), name='order-history'),

    # Payments
    path('payments/', PaymentListView.as_view(), name='user-payments'),
    path('payments/record/', record_payment, name='record-payment'),
    path('webhook/razorpay/', razorpay_webhook, name='razorpay-webhook'),

    # Razorpay Order Creation & Verification
    path('create-order/', create_order, name='create-order'),
    path('verify-payment/', verify_payment, name='verify-payment'),
]
