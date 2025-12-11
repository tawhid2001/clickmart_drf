from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import CartSerializer
from .models import Cart

# Create your views here.


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # get or create cart for the authenticated user
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)