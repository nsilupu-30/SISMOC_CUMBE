"""Consulta y revisión de jornadas sin sobrescribir los resultados de origen."""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from asistencia.models import (
    MarcacionBiometrica, ResumenAsistenciaDiaria, RevisionAsistencia,
    CierreAsistencia,
)

CONCEPTOS_HORAS = ("horas_trabajadas", "horas_extras_25", "horas_extras_35", "horas_nocturnas")
GESTORES = {"ADMINISTRADOR", "CONTADORA", "GERENTE_GENERAL"}


def puede_gestionar(usuario):
    return usuario.is_active and usuario.esta_activo and (usuario.is_superuser or usuario.rol in GESTORES)


def puede_aprobar(usuario):
    return puede_gestionar(usuario) and (usuario.is_superuser or usuario.rol in {"CONTADORA", "GERENTE_GENERAL"})


def estado_revision(resumen):
    if resumen.verificado_contabilidad:
        return "APROBADO"
    return "OBSERVADO" if resumen.estado_revision == "OBSERVADO" else "PENDIENTE"


def comprobar_abierto(fecha):
    if CierreAsistencia.objects.filter(fecha_inicio__lte=fecha, fecha_fin__gte=fecha).exists():
        raise ValidationError("La jornada pertenece a un periodo cerrado. No se pueden modificar sus datos.")


def registrar_historial(resumen, actor, accion, detalle="", marcacion=None):
    return RevisionAsistencia.objects.create(
        resumen=resumen, responsable=actor, accion=accion, detalle=detalle, marcacion=marcacion,
    )


def dejar_pendiente(resumen, actor, motivo):
    resumen.estado_revision = "PENDIENTE"
    resumen.verificado_contabilidad = False
    resumen.revisado_por = None
    resumen.fecha_revision = None
    resumen.save(update_fields=["estado_revision", "verificado_contabilidad", "revisado_por", "fecha_revision"])
    registrar_historial(resumen, actor, "Revisión pendiente", motivo)


def valores_ajustados(resumen):
    valores = {key: Decimal(str(getattr(resumen, key))) for key in CONCEPTOS_HORAS}
    valores.update(descanso_feriado=Decimal(0), descuento=Decimal(0), compensacion=Decimal(0))
    for ajuste in resumen.ajustes.all():
        if ajuste.aprobado_el:
            valores[ajuste.concepto] += Decimal(ajuste.minutos) / Decimal(60)
    return valores


def ventana_jornada(resumen):
    """Usa los límites guardados; nunca une arbitrariamente todas las marcas de dos días."""
    turno = resumen.turno_aplicado or resumen.usuario.turno
    inicio = datetime.combine(resumen.fecha, resumen.primera_entrada or datetime.min.time())
    if resumen.ultima_salida and resumen.primera_entrada:
        fin = datetime.combine(resumen.fecha, resumen.ultima_salida)
        if fin < inicio:
            fin += timedelta(days=1)
    else:
        fin = datetime.combine(resumen.fecha + timedelta(days=1), datetime.min.time())
        if turno and turno.hora_salida < turno.hora_entrada:
            fin = datetime.combine(resumen.fecha + timedelta(days=1), turno.hora_salida)
    return timezone.make_aware(inicio), timezone.make_aware(fin)


def detalle_jornada(resumen):
    turno = resumen.turno_aplicado or resumen.usuario.turno
    inicio, fin = ventana_jornada(resumen)
    marcas = list(MarcacionBiometrica.objects.filter(
        Q(usuario_id=resumen.usuario_id) | Q(usuario__isnull=True, dni=resumen.usuario.dni),
        fecha_hora__gte=inicio, fecha_hora__lte=fin,
    ).select_related("carga_origen", "correccion_evento").order_by("fecha_hora", "pk"))
    alertas, tramos = [], []
    entrada = refrigerio = None
    trabajo_seg = refrigerio_seg = 0
    completa = True
    validas = [m for m in marcas if m.es_valida]
    for marca in marcas:
        correccion = getattr(marca, "correccion_evento", None)
        marca.evento_efectivo = correccion.tipo_evento if correccion else marca.tipo_evento
        marca.evento_etiqueta = dict(MarcacionBiometrica.TipoEvento.choices).get(marca.evento_efectivo, marca.evento_efectivo)
        marca.fecha_local = timezone.localtime(marca.fecha_hora)
        if not marca.es_valida:
            continue
        tipo = marca.evento_efectivo
        if tipo == "ENTRADA":
            if entrada or refrigerio:
                completa = False
            entrada = marca.fecha_hora
        elif tipo == "SALIDA_REFRIGERIO":
            if entrada is None or refrigerio:
                completa = False
            else:
                segundos = (marca.fecha_hora - entrada).total_seconds()
                trabajo_seg += segundos
                tramos.append({"inicio": timezone.localtime(entrada), "fin": marca.fecha_local, "duracion": duracion(segundos)})
                entrada = None
            refrigerio = marca.fecha_hora
        elif tipo == "RETORNO_REFRIGERIO":
            if refrigerio is None or entrada:
                completa = False
            else:
                refrigerio_seg += (marca.fecha_hora - refrigerio).total_seconds()
            refrigerio = None
            entrada = marca.fecha_hora
        elif tipo == "SALIDA":
            if entrada is None or refrigerio:
                completa = False
            else:
                segundos = (marca.fecha_hora - entrada).total_seconds()
                trabajo_seg += segundos
                tramos.append({"inicio": timezone.localtime(entrada), "fin": marca.fecha_local, "duracion": duracion(segundos)})
            entrada = None
        else:
            completa = False
    completa = bool(validas) and completa and entrada is None and refrigerio is None
    if not validas:
        alertas.append("No hay marcaciones válidas en el intervalo de la jornada.")
    elif not completa:
        alertas.append("Marcaciones incompletas o tipos de evento inconsistentes. Revise entrada, refrigerio y salida.")
    if not turno:
        alertas.append("Trabajador sin turno asignado.")
    if resumen.primera_entrada and resumen.ultima_salida and resumen.ultima_salida < resumen.primera_entrada:
        alertas.append("La salida se consulta al día siguiente porque su hora es anterior a la entrada. Confirme el cruce de medianoche.")
    if completa and abs(Decimal(str(trabajo_seg / 3600)) - resumen.horas_trabajadas) > Decimal("0.02"):
        alertas.append("Las horas guardadas difieren del tiempo reconstruido por marcaciones. Registre un ajuste si corresponde.")
    valores = valores_ajustados(resumen)
    if any(valores[key] < 0 for key in CONCEPTOS_HORAS + ("descanso_feriado", "descuento", "compensacion")):
        alertas.append("Hay un concepto con total negativo. Revise los ajustes.")
    pendientes = any(not i.aprobado_el for i in resumen.incidencias.all()) or any(not a.aprobado_el for a in resumen.ajustes.all())
    if pendientes:
        alertas.append("Existen incidencias o ajustes pendientes de aprobación.")
    justificada = resumen.horas_trabajadas == 0 and resumen.estado in {"VACACIONES", "PERMISO", "DESCANSO_MEDICO", "DIA_LIBRE", "DESCANSO_SUTRAN", "FALTA"}
    if justificada and resumen.estado != "FALTA":
        justificada = any(i.aprobado_el and i.minutos is None for i in resumen.incidencias.all())
    diferencia = completa and abs(Decimal(str(trabajo_seg / 3600)) - valores["horas_trabajadas"]) > Decimal("0.02")
    deficit = None
    if completa and turno:
        base_inicio = datetime.combine(resumen.fecha, turno.hora_entrada)
        base_fin = datetime.combine(resumen.fecha, turno.hora_salida)
        if base_fin <= base_inicio:
            base_fin += timedelta(days=1)
        base = (base_fin - base_inicio).total_seconds()
        if turno.hora_inicio_refrigerio and turno.hora_fin_refrigerio:
            ref_inicio = datetime.combine(resumen.fecha, turno.hora_inicio_refrigerio)
            ref_fin = datetime.combine(resumen.fecha, turno.hora_fin_refrigerio)
            if ref_fin < ref_inicio:
                ref_fin += timedelta(days=1)
            base -= (ref_fin - ref_inicio).total_seconds()
        deficit = max(0, round((base - trabajo_seg) / 60))
    bloqueos = []
    if not completa and not justificada:
        bloqueos.append("Complete o corrija las marcaciones; una ausencia justificada requiere una incidencia de día completo aprobada.")
    if not turno and not justificada:
        bloqueos.append("Asigne el turno del trabajador.")
    if diferencia:
        bloqueos.append("Concilie las horas efectivas con los tramos mediante un ajuste.")
    if pendientes:
        bloqueos.append("Apruebe las incidencias y los ajustes pendientes.")
    if any(v < 0 for v in valores.values()):
        bloqueos.append("Los conceptos no pueden quedar con total negativo.")
    return {
        "resumen": resumen, "turno": turno, "marcas": marcas, "tramos": tramos,
        "alertas": alertas, "bloqueos": bloqueos, "completa": completa,
        "refrigerio": duracion(refrigerio_seg) if completa else None,
        "trabajo_reconstruido": duracion(trabajo_seg) if completa else None,
        "deficit_minutos": deficit,
        "valores": valores, "revision": estado_revision(resumen),
        "cerrada": CierreAsistencia.objects.filter(fecha_inicio__lte=resumen.fecha, fecha_fin__gte=resumen.fecha).exists(),
        "inicio_consulta": timezone.localtime(inicio), "fin_consulta": timezone.localtime(fin),
    }


def duracion(segundos):
    segundos = int(round(segundos))
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}:{segundos % 60:02d}"


def revisar(resumen, actor, decision, motivo=""):
    comprobar_abierto(resumen.fecha)
    if decision == "APROBADO":
        if not puede_aprobar(actor):
            raise ValidationError("La aprobación corresponde a Contabilidad o Gerencia.")
        bloqueos = detalle_jornada(resumen)["bloqueos"]
        if bloqueos:
            raise ValidationError(bloqueos)
    elif decision == "OBSERVADO":
        if not puede_gestionar(actor):
            raise ValidationError("No tiene permiso para observar jornadas.")
        if not motivo.strip():
            raise ValidationError("Indique el motivo de la observación.")
    else:
        raise ValidationError("Estado de revisión no válido.")
    resumen.estado_revision = decision
    resumen.verificado_contabilidad = decision == "APROBADO"
    resumen.revisado_por = actor
    resumen.fecha_revision = timezone.now()
    resumen.save(update_fields=["estado_revision", "verificado_contabilidad", "revisado_por", "fecha_revision"])
    registrar_historial(resumen, actor, "Jornada aprobada" if decision == "APROBADO" else "Jornada observada", motivo)
