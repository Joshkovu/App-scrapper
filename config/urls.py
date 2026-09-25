from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from reviews.auth import EmailTokenObtainPairView, SignupView
from reviews.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/signup/", SignupView.as_view(), name="signup"),
    path("api/auth/login/", EmailTokenObtainPairView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/apps/", include("reviews.urls")),
]
