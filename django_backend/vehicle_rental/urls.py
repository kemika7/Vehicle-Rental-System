from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from employees.views import CustomTokenObtainPairView, RegisterView, MeView

urlpatterns = [
    # ── Django admin ──────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path("api/auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/me/", MeView.as_view(), name="me"),

    # ── API resources ─────────────────────────────────────────────────────────
    path("api/", include("offices.urls")),
    path("api/", include("employees.urls")),
    path("api/", include("vehicles.urls")),
    path("api/", include("rentals.urls")),
]
