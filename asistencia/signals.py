"""Invalidar revisiones al cambiar sus fuentes y proteger periodos cerrados."""
from datetime import timedelta
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from asistencia.models import (
    ResumenAsistenciaDiaria, MarcacionBiometrica, IncidenciaAsistencia,
    AjusteAsistencia, CorreccionEvento, RevisionAsistencia,
)
from asistencia.services.revision import comprobar_abierto, ventana_jornada


def fechas_marca(instance):
    dia = timezone.localtime(instance.fecha_hora).date()
    comprobar_abierto(dia)
    for r in ResumenAsistenciaDiaria.objects.filter(usuario_id=instance.usuario_id, fecha=dia - timedelta(days=1)):
        inicio, fin = ventana_jornada(r)
        if inicio <= instance.fecha_hora <= fin:
            comprobar_abierto(r.fecha)


@receiver(pre_save, sender=ResumenAsistenciaDiaria)
def proteger_resumen(sender, instance, **kwargs):
    comprobar_abierto(instance.fecha)
    if instance.pk:
        original = sender.objects.filter(pk=instance.pk).first()
        if original:
            comprobar_abierto(original.fecha)
            campos = ("usuario_id", "fecha", "primera_entrada", "ultima_salida", "horas_trabajadas", "horas_extras_25", "horas_extras_35", "horas_nocturnas", "minutos_tardanza", "turno_aplicado_id", "estado", "observaciones")
            if any(getattr(original, c) != getattr(instance, c) for c in campos):
                sender.objects.filter(pk=instance.pk).update(verificado_contabilidad=False, estado_revision="PENDIENTE", revisado_por=None, fecha_revision=None)
                instance.verificado_contabilidad = False
                instance.estado_revision = "PENDIENTE"
                instance.revisado_por = instance.fecha_revision = None
                RevisionAsistencia.objects.create(resumen=original, accion="Datos modificados", detalle="La jornada requiere una nueva revisión por cambios en sus datos.")


@receiver(pre_save, sender=MarcacionBiometrica)
def proteger_marca(sender, instance, **kwargs):
    fechas_marca(instance)
    if instance.pk:
        original = sender.objects.filter(pk=instance.pk).first()
        if original:
            fechas_marca(original)
            instance._marca_anterior = original


@receiver(pre_save, sender=IncidenciaAsistencia)
@receiver(pre_save, sender=AjusteAsistencia)
@receiver(pre_save, sender=CorreccionEvento)
def proteger_evidencia(sender, instance, **kwargs):
    if isinstance(instance, CorreccionEvento):
        fechas_marca(instance.marcacion)
    else:
        comprobar_abierto(instance.resumen.fecha)


@receiver(post_save, sender=MarcacionBiometrica)
@receiver(post_save, sender=CorreccionEvento)
@receiver(post_delete, sender=MarcacionBiometrica)
@receiver(post_delete, sender=CorreccionEvento)
def invalidar_por_marcacion(sender, instance, **kwargs):
    marca = instance.marcacion if isinstance(instance, CorreccionEvento) else instance
    for fuente in [marca, getattr(marca, "_marca_anterior", marca)]:
        dia = timezone.localtime(fuente.fecha_hora).date()
        qs = ResumenAsistenciaDiaria.objects.filter(usuario_id=fuente.usuario_id, fecha__range=(dia - timedelta(days=1), dia))
        for r in qs:
            inicio, fin = ventana_jornada(r)
            if inicio <= fuente.fecha_hora <= fin and r.verificado_contabilidad:
                ResumenAsistenciaDiaria.objects.filter(pk=r.pk).update(verificado_contabilidad=False, estado_revision="PENDIENTE", revisado_por=None, fecha_revision=None)
                RevisionAsistencia.objects.create(resumen=r, accion="Marcaciones modificadas", detalle="Se requiere una nueva revisión.")


@receiver(post_save, sender=IncidenciaAsistencia)
@receiver(post_save, sender=AjusteAsistencia)
@receiver(post_delete, sender=IncidenciaAsistencia)
@receiver(post_delete, sender=AjusteAsistencia)
def invalidar_por_evidencia(sender, instance, **kwargs):
    qs = ResumenAsistenciaDiaria.objects.filter(pk=instance.resumen_id, verificado_contabilidad=True)
    if qs.update(verificado_contabilidad=False, estado_revision="PENDIENTE", revisado_por=None, fecha_revision=None):
        RevisionAsistencia.objects.create(resumen_id=instance.resumen_id, accion="Evidencia modificada", detalle="Se requiere una nueva revisión por cambios en incidencias o ajustes.")


@receiver(pre_delete, sender=ResumenAsistenciaDiaria)
@receiver(pre_delete, sender=MarcacionBiometrica)
@receiver(pre_delete, sender=IncidenciaAsistencia)
@receiver(pre_delete, sender=AjusteAsistencia)
@receiver(pre_delete, sender=CorreccionEvento)
def proteger_eliminacion(sender, instance, **kwargs):
    if isinstance(instance, ResumenAsistenciaDiaria):
        comprobar_abierto(instance.fecha)
    elif isinstance(instance, MarcacionBiometrica):
        fechas_marca(instance)
    else:
        proteger_evidencia(sender, instance)
