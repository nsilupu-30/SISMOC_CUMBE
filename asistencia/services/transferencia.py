"""Publicar jornadas de fichas identificadas, sin crear cuentas ni inventar tiempos."""
import re
from datetime import timedelta, time
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from asistencia.models import Trabajador, ResumenAsistenciaDiaria, MarcacionBiometrica
from asistencia.services.revision import comprobar_abierto, registrar_historial, detalle_jornada
from asistencia.services.cuadro_excel import segundos_nocturnos, base_jornada_segundos
from asistencia.services.horarios import turno_programado, actualizar_tardanza


@transaction.atomic
def pasar_a_asistencia(trabajadores_ids, desde, hasta, actor, *, marcas_ids=None):
    fichas = list(Trabajador.objects.select_for_update().filter(pk__in=trabajadores_ids).order_by("pk"))
    if not fichas:
        raise ValidationError("No hay trabajadores identificados para enviar con estos filtros.")
    nuevas = existentes = 0
    fechas = []
    for ficha in fichas:
        if not re.fullmatch(r"[0-9]{8}", ficha.dni) or len(ficha.nombre_completo.split()) < 2 or not ficha.area.strip() or ficha.area.strip().casefold() == "por completar":
            raise ValidationError(f"Complete nombre, DNI y área de {ficha.nombre_completo} antes de enviar.")
        marcas = MarcacionBiometrica.objects.filter(
            Q(identidad_biometrica__trabajador=ficha) | Q(filas_origen__identidad__trabajador=ficha),
            fecha_hora__date__range=(desde - timedelta(days=1), hasta + timedelta(days=1)), es_valida=True,
        ).select_related("identidad_biometrica", "correccion_evento").prefetch_related("filas_origen__identidad").order_by("fecha_hora", "pk").distinct()
        if marcas_ids is not None:
            marcas = marcas.filter(pk__in=marcas_ids)
        dias = {}
        abierta = None
        horarios = {}
        def horario(dia):
            if dia not in horarios:
                horarios[dia] = turno_programado(ficha, dia)
            return horarios[dia]
        def dia_programado(local):
            anterior = local.date() - timedelta(days=1)
            previo, actual = horario(anterior), horario(local.date())
            if previo and previo.hora_salida < previo.hora_entrada:
                # Punto medio del descanso entre turnos: admite ingresos anticipados
                # y salidas posteriores sin separar la jornada en medianoche.
                mitad = ((previo.hora_salida.hour*60+previo.hora_salida.minute)+(previo.hora_entrada.hour*60+previo.hora_entrada.minute))//2
                if local.time() < time(mitad//60,mitad%60):
                    if not actual or actual.hora_salida < actual.hora_entrada or local.time() < actual.hora_entrada:
                        return anterior
            return local.date()
        for marca in marcas:
            local = timezone.localtime(marca.fecha_hora)
            evento = getattr(getattr(marca, "correccion_evento", None), "tipo_evento", marca.tipo_evento)
            fecha_programada = dia_programado(local) if evento == 'SIN_CLASIFICAR' else local.date()
            if abierta and evento == 'SIN_CLASIFICAR' and fecha_programada != abierta:
                abierta = None
            if fecha_programada > hasta and abierta is None:
                continue
            if local.date() > hasta and abierta is not None and (local.date() - abierta).days > 1:
                continue
            propietarios = {f.identidad.trabajador_id for f in marca.filas_origen.all() if f.identidad.trabajador_id}
            if marca.identidad_biometrica_id and marca.identidad_biometrica.trabajador_id:
                propietarios.add(marca.identidad_biometrica.trabajador_id)
            if len(propietarios) > 1 or (marca.usuario_id and marca.usuario_id != ficha.usuario_id):
                raise ValidationError(f"Hay una marcación del código asociada a otra persona. Revise {ficha.nombre_completo} antes de enviar.")
            if evento == "ENTRADA":
                abierta = local.date()
            dia = abierta or fecha_programada
            if desde <= dia <= hasta:
                dias.setdefault(dia, []).append(marca)
            if evento == "SALIDA":
                abierta = None
        for dia, registros in dias.items():
            comprobar_abierto(dia)
            for marca in registros:
                comprobar_abierto(timezone.localtime(marca.fecha_hora).date())
            consulta = Q(trabajador=ficha)
            if ficha.usuario_id:
                consulta |= Q(usuario_id=ficha.usuario_id)
            existente = ResumenAsistenciaDiaria.objects.filter(consulta, fecha=dia).first()
            if existente:
                existentes += 1
                fechas.append(dia)
                continue
            primera, ultima = registros[0], registros[-1]
            resumen = ResumenAsistenciaDiaria.objects.create(
                trabajador=ficha, usuario_id=ficha.usuario_id, fecha=dia,
                marcaciones_publicadas=[m.pk for m in registros] if marcas_ids is not None else None,
                primera_entrada=timezone.localtime(primera.fecha_hora).time(),
                ultima_salida=timezone.localtime(ultima.fecha_hora).time() if primera.pk != ultima.pk else None,
                turno_aplicado=turno_programado(ficha, dia),
                estado="POR_REVISAR",
                observaciones="Enviada desde Importador Excel. Primera y última marca delimitan la consulta; confirmar eventos, refrigerio y horario. Tiempos pendientes de conciliación.",
            )
            detalle = detalle_jornada(resumen)
            if detalle["completa"]:
                trabajo = sum((tramo["fin"] - tramo["inicio"]).total_seconds() for tramo in detalle["tramos"])
                valores = {
                    "horas_trabajadas": Decimal(str(trabajo / 3600)).quantize(Decimal("0.01")),
                    "horas_nocturnas": Decimal(str(segundos_nocturnos(detalle["tramos"]) / 3600)).quantize(Decimal("0.01")),
                }
                base = base_jornada_segundos()
                if base is not None:
                    extras = max(0, trabajo - base)
                    valores.update(horas_extras_25=Decimal(str(min(extras, 7200) / 3600)).quantize(Decimal("0.01")), horas_extras_35=Decimal(str(max(extras - 7200, 0) / 3600)).quantize(Decimal("0.01")))
                for campo, valor in valores.items():
                    setattr(resumen, campo, valor)
                resumen.save(update_fields=list(valores))
            actualizar_tardanza(resumen, detalle)
            registrar_historial(resumen, actor, "Marcaciones enviadas a Asistencia", f"Trabajador #{ficha.pk}; {len(registros)} marcas. No se modificaron los eventos originales ni se aprobaron horas.")
            nuevas += 1
            fechas.append(dia)
        from asistencia.services.jornadas_nocturnas import reagrupar_nocturnas
        reagrupar_nocturnas(ficha, dias.keys(), actor)
    if not fechas:
        raise ValidationError("No hay marcaciones válidas en el periodo seleccionado.")
    return {"nuevas": nuevas, "existentes": existentes, "desde": min(fechas), "hasta": max(fechas)}
