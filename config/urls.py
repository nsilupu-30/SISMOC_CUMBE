# ==============================================================================
# config/urls.py
# SISMOC-CUMBE | Enrutador Principal de URLs
# Empresa de Transportes El Cumbe S.A.C. - RUC: 20480397731
# ==============================================================================

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from config.api import api
from core.views import dashboard_view, login_view, logout_view

urlpatterns = [
    # Dashboard Web Principal (Sprint 1)
    path("", dashboard_view, name="dashboard"),

    # Autenticacion Institucional y Cierre de Sesion (7 Roles RBAC)
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Panel de Administracion de Django
    path("admin/", admin.site.urls),

    # API REST con Django Ninja (Documentacion interactiva en /api/docs)
    path("api/", api.urls),
]

# Servir archivos media en desarrollo (fotos de peajes, archivos Excel)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
