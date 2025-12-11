from django.urls import path
from users import views as UserViews
from products import views as ProductViews
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Define your API URL patterns here
    # User API endpoints
    path('register/', UserViews.RegisterView.as_view()),
    path('profile/', UserViews.ProfileView.as_view()),
    
    # JWT Authentication endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Product API endpoints
    # product list
    path('products/', ProductViews.ProductListView.as_view()),
    # product detail
    path('products/<int:pk>/', ProductViews.ProductDetailView.as_view()),
]