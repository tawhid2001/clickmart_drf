from decimal import Decimal
from django.shortcuts import render
from .serializers import OrderSerializer, OrderItemSerializer
from carts.models import Cart, CartItem
from .models import Order, OrderItem
from .serializers import OrderSerializer
from .utils import send_order_notification
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView

# Create your views here.


class PlaceOrderView(APIView):
    # the user must be logged in
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # check if the cart is empty
        cart = Cart.objects.get(user=request.user)
        shipping_address = request.data.get("shippingAddress")
        if not cart or cart.items.count() == 0:
            return Response({'error': 'Cart is empty'})
            
        
        # create the order
        order = Order.objects.create(
            user = request.user,
            subtotal = Decimal(cart.subtotal),
            tax_amount = Decimal(cart.tax_amount),
            grand_total = Decimal(cart.grand_total),
            address = shipping_address.get("address"),
            phone = shipping_address.get("phone"),
            city = shipping_address.get("city"),
            state = shipping_address.get("state"),
            zip_code = shipping_address.get("zipCode"),
        )
        
        # Loop through the cart items 
        for item in cart.items.all():
            # reduce the product stock
            product = item.product
            if product.stock < item.quantity:
                return Response({'error': f'Product {product.name} is out of stock'}, status=status.HTTP_400_BAD_REQUEST)
            product.stock -= item.quantity
            product.save()
        
        # create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order = order,
                product = item.product,
                quantity = item.quantity,
                price = Decimal(item.product.price),
                total_price = Decimal(item.total_price)
            )
        
        # clear the cart items
        
        Cart.objects.all().delete()
        cart.save()
        
        # send the notification email
        send_order_notification(order=order)
        
        # send the response to frontend
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class MyOrdersView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
class MyOrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    