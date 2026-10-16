# ==============================================================================
# config/urls.py
# SISMOC-CUMBE | Enrutador Principal de URLs
# ==============================================================================

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from config.api import api
from core.views import dashboard_view

urlpatterns = [
    # Dashboard Web Principal (Sprint 1)
    path("", dashboard_view, name="dashboard"),

    # Panel de Administración de Django
    path("admin/", admin.site.urls),

    # API REST con Django Ninja (Documentación interactiva en /api/docs)
    path("api/", api.urls),
]

# Servir archivos media en desarrollo (fotos de peajes, archivos Excel)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
