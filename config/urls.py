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
from asistencia import views as asistencia_views
from asistencia import views_trabajadores
from asistencia import views_revision_trabajador

urlpatterns = [
    path("asistencia/aprobar-periodo-trabajador/", views_revision_trabajador.aprobar_periodo_trabajador, name="aprobar_periodo_trabajador"),
    path("asistencia/registrar-dia-sin-marcas/", views_revision_trabajador.registrar_dia_sin_marcas, name="registrar_dia_sin_marcas"),
    path("asistencia/validar-marcaciones-trabajador/", views_revision_trabajador.validar_marcaciones_trabajador, name="validar_marcaciones_trabajador"),
    path("asistencia/enviar-importadas/", views_trabajadores.enviar_a_asistencia, name="enviar_a_asistencia"),
    path("asistencia/trabajadores/buscar/", views_trabajadores.buscar_trabajadores, name="buscar_trabajadores"),
    path("asistencia/identidad/<int:identidad_id>/confirmar/", views_trabajadores.confirmar_trabajador, name="confirmar_trabajador"),
    path("asistencia/identidad/<int:identidad_id>/registrar/", views_trabajadores.registrar_trabajador, name="registrar_trabajador"),
    path("asistencia/identidad/<int:identidad_id>/editar/", views_trabajadores.editar_trabajador, name="editar_trabajador"),
    # Dashboard Web Principal (Sprint 1)
    path("", dashboard_view, name="dashboard"),

    # Autenticacion Institucional y Cierre de Sesion (7 Roles RBAC)
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("asistencia/jornada/<int:resumen_id>/", asistencia_views.accion_jornada, name="accion_jornada"),
    path("asistencia/marcacion/<int:marcacion_id>/asociar/", asistencia_views.asociar_marcacion, name="asociar_marcacion"),
    path("asistencia/exportar/", asistencia_views.exportar_asistencia, name="exportar_asistencia"),
    path("asistencia/cerrar-periodo/", asistencia_views.cerrar_periodo, name="cerrar_periodo"),
    path("asistencia/crear-jornada/", asistencia_views.crear_jornada, name="crear_jornada"),
    path("asistencia/consultar-huellero/", asistencia_views.consultar_huellero, name="consultar_huellero"),
    path("asistencia/registros-huellero/", asistencia_views.registros_huellero, name="registros_huellero"),
    path("asistencia/importar/", asistencia_views.importar_excel_web, name="importar_excel_web"),
    path("asistencia/identidad/<int:identidad_id>/", asistencia_views.vincular_identidad, name="vincular_identidad"),
    path("asistencia/marcar/", asistencia_views.marcar_web, name="marcar_web"),

    # Panel de Administracion de Django
    path("admin/", admin.site.urls),

    # API REST con Django Ninja (Documentacion interactiva en /api/docs)
    path("api/", api.urls),
]

# Servir archivos media en desarrollo (fotos de peajes, archivos Excel)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
