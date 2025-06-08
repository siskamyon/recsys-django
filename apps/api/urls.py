from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ContentSourceViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sources', ContentSourceViewSet, basename='source')

urlpatterns = [
    path('', include(router.urls)),
]