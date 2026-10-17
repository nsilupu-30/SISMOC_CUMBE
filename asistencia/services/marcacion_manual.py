"""Registro explícito de una marcación faltante, con procedencia y auditoría."""
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from asistencia.forms import MarcacionManualForm
from asistencia.models import MarcacionBiometrica, ResumenAsistenciaDiaria
from asistencia.services.revision import comprobar_abierto, detalle_jornada, marcas_persona, ventana_jornada, registrar_historial, dejar_pendiente
from asistencia.services.revision_trabajador import filtrar_persona, validar_periodo


def agregar_marcacion_manual(resumen, datos, actor):
    """El llamador bloquea la jornada y mantiene una transacción."""
    formulario = MarcacionManualForm(datos, resumen=resumen)
    if not formulario.is_valid():
        raise ValidationError([f"{formulario.fields[campo].label}: {mensaje}" for campo, mensajes in formulario.errors.items() for mensaje in mensajes])
    valores = formulario.cleaned_data
    fecha = valores["fecha_manual"]
    instante = timezone.make_aware(datetime.combine(fecha, valores["hora_manual"]))
    if fecha not in {resumen.fecha, resumen.fecha + timedelta(days=1)}:
        raise ValidationError("La fecha debe corresponder a la jornada o al día siguiente si cruza medianoche.")
    if instante > timezone.now():
        raise ValidationError("No se puede agregar una marcación con fecha u hora futura.")
    comprobar_abierto(resumen.fecha)
    comprobar_abierto(fecha)
    if detalle_jornada(resumen)["situacion_dia"]:
        raise ValidationError("El día tiene una situación de no laborado registrada. Revise esa situación antes de agregar trabajo.")
    identidad = valores["identidad_manual"]
    if resumen.trabajador_id and identidad is None:
        raise ValidationError("Seleccione el código importado que identifica al trabajador.")
    if MarcacionBiometrica.objects.filter(marcas_persona(resumen), fecha_hora=instante, es_valida=True).exists():
        raise ValidationError("El trabajador ya tiene una marcación a esa fecha y hora. Corrija el tipo de la existente.")
    otras = filtrar_persona(ResumenAsistenciaDiaria.objects.all(), resumen.persona.dni).filter(fecha__range=(resumen.fecha - timedelta(days=1), fecha)).exclude(pk=resumen.pk)
    for otra in otras:
        inicio, fin = ventana_jornada(otra)
        if inicio <= instante <= fin:
            raise ValidationError("La hora corresponde al intervalo de otra jornada del trabajador. Agréguela en el día correcto.")
    originales = detalle_jornada(resumen)["marcas"]
    instantes = [m.fecha_hora for m in originales if m.es_valida] + [instante]
    primera, ultima = min(instantes), max(instantes)
    if timezone.localtime(primera).date() != resumen.fecha or ultima - primera >= timedelta(days=1):
        raise ValidationError("La marcación produciría una jornada de 24 horas o más, o una entrada en otro día. Revise la fecha y hora.")
    codigo = identidad.codigo if identidad else None
    marca = MarcacionBiometrica.objects.create(
        usuario_id=resumen.usuario_id, identidad_biometrica=identidad,
        dni=resumen.persona.dni, nombre_empleado=resumen.persona.nombre_completo,
        zkteco_user_id=int(codigo) if codigo and codigo.isdigit() and len(codigo) <= 9 else None,
        fecha_hora=instante, tipo_evento=valores["tipo_evento_manual"], origen="SISTEMA_MANUAL",
        registrada_por=actor, motivo_manual=valores["motivo_manual"], evidencia_manual_url=valores["evidencia_manual_url"],
    )
    resumen.primera_entrada = timezone.localtime(primera).time()
    resumen.ultima_salida = timezone.localtime(ultima).time() if primera != ultima else None
    resumen.save(update_fields=["primera_entrada", "ultima_salida"])
    registrar_historial(resumen, actor, "Marcación manual agregada", f"{instante.isoformat()} · {marca.get_tipo_evento_display()} · {valores['motivo_manual']}", marca)
    dejar_pendiente(resumen, actor, "Se agregó una marcación manual; requiere revisión de la jornada.")
    validar_periodo([resumen], {}, {}, None, "Recalculado tras agregar marcación manual.", actor)
    return marca
