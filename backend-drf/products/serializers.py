from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        
    def get_image(self, obj):
        print("Serializing image for product:", obj.name, "Image field:", obj.image)
        return obj.image.url if obj.image else None