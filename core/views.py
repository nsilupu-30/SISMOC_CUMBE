# core/views.py
# SISMOC-CUMBE | Vista del Dashboard Principal de Gestión (Sprint 1)

from django.shortcuts import render
from django.conf import settings
from core.models import Usuario
from asistencia.models import MarcacionBiometrica, ResumenAsistenciaDiaria, TurnoHorario
from asistencia.services.zkteco_live import ZKTecoLiveClient


def dashboard_view(request):
    """Vista web principal para monitoreo en vivo de SISMOC-CUMBE."""
    # Obtener estado en tiempo real del reloj ZKTeco
    client = ZKTecoLiveClient()
    info_huellero = client.sincronizar_marcaciones_en_vivo()

    # Resumen general para la cabecera
    total_usuarios = Usuario.objects.filter(esta_activo=True).count()
    total_conductores = Usuario.objects.filter(rol=Usuario.Rol.CONDUCTOR, esta_activo=True).count()
    resumenes_recientes = ResumenAsistenciaDiaria.objects.select_related("usuario").order_by("-fecha")[:25]
    turnos = TurnoHorario.objects.filter(activo=True)

    context = {
        "empresa_nombre": "EMPRESA DE TRANSPORTES EL CUMBE S.A.C.",
        "empresa_ruc": "20480397731",
        "info_huellero": info_huellero,
        "total_usuarios": total_usuarios,
        "total_conductores": total_conductores,
        "resumenes_recientes": resumenes_recientes,
        "turnos": turnos,
        "roles": Usuario.Rol.choices,
    }
    return render(request, "index.html", context)
