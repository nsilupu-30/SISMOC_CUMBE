"""Confirmación explícita de la situación de un día sin trabajo."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from asistencia.models import IncidenciaAsistencia
from asistencia.services.revision import puede_aprobar, comprobar_abierto, detalle_jornada, registrar_historial, revisar

ESTADOS = {'DESCANSO_SEMANAL':'DIA_LIBRE','FERIADO_NO_LABORADO':'FERIADO','PERMISO':'PERMISO','VACACIONES':'VACACIONES','DESCANSO_MEDICO':'DESCANSO_MEDICO','CAMBIO_DESCANSO':'DIA_LIBRE'}


@transaction.atomic
def aprobar_situacion_del_dia(resumen, actor, tipo, motivo=''):
    """El llamador bloquea la jornada dentro de una transacción."""
    if not puede_aprobar(actor):
        raise ValidationError('Solo Contabilidad o Gerencia puede aprobar el día.')
    comprobar_abierto(resumen.fecha)
    if tipo not in ESTADOS:
        raise ValidationError('Seleccione la situación del día antes de aprobarlo.')
    if tipo=='PERMISO' and not motivo.strip():
        raise ValidationError('Indique la justificación del permiso.')
    d=detalle_jornada(resumen,incluir_formulario=False)
    if resumen.verificado_contabilidad:
        raise ValidationError('El día ya está aprobado. Reábralo antes de modificar su situación.')
    if not d['solo_situacion'] or any(m.es_valida for m in d['marcas']):
        raise ValidationError('La jornada tiene marcaciones o ajustes. Revísela desde su detalle.')
    situacion=d['situacion_dia']
    anterior=f'{situacion.get_tipo_display()}: {situacion.motivo}; aprobación: {situacion.aprobado_el or "pendiente"}'
    situacion.tipo=tipo
    situacion.motivo=motivo.strip() if tipo=='PERMISO' else dict(IncidenciaAsistencia.TIPOS)[tipo]
    situacion.aprobado_por=actor
    situacion.aprobado_el=timezone.now()
    situacion.full_clean()
    situacion.save(update_fields=['tipo','motivo','aprobado_por','aprobado_el'])
    resumen.estado=ESTADOS[tipo]
    resumen.save(update_fields=['estado'])
    registrar_historial(resumen,actor,'Situación confirmada para aprobación',f'Anterior: {anterior}. Selección: {situacion.get_tipo_display()}; {situacion.motivo}.')
    revisar(resumen,actor,'APROBADO',f'Situación seleccionada: {situacion.get_tipo_display()}. {situacion.motivo}',situacion_confirmada=tipo)
