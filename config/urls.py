from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# DRF va Swagger uchun importlar
from rest_framework.routers import DefaultRouter
from shop.views import CategoryViewSet, ProductViewSet, OrderViewSet
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions

# Routerlarni sozlash
router = DefaultRouter()
router.register(r'api-categories', CategoryViewSet)
router.register(r'api-products', ProductViewSet)
router.register(r'api-orders', OrderViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Online Do'kon API",
      default_version='v1',
      description="Kurs ishi API hujjatlari",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Asosiy yo'llar
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('users/', include('users.urls')),

    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # API yo'llari
    path('api/v1/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)