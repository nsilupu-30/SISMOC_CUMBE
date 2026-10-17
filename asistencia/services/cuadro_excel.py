"""Cuadro diario con columnas equivalentes al control individual del Excel."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.utils import timezone


def formato_tiempo(segundos):
    if segundos is None:
        return "Por revisar"
    cantidad = int(round(segundos))
    signo = "−" if cantidad < 0 else ""
    cantidad = abs(cantidad)
    return f"{signo}{cantidad // 3600:02d}:{cantidad % 3600 // 60:02d}:{cantidad % 60:02d}"


def base_jornada_segundos():
    """Jornada efectiva de 8 horas definida para el control de asistencia."""
    return 8 * 3600


def segundos_nocturnos(tramos):
    total = 0
    for tramo in tramos:
        inicio, fin = tramo["inicio"], tramo["fin"]
        dia = inicio.date()
        while dia <= fin.date():
            medianoche = timezone.make_aware(datetime.combine(dia, time.min))
            seis = timezone.make_aware(datetime.combine(dia, time(6)))
            veintidos = timezone.make_aware(datetime.combine(dia, time(22)))
            siguiente = timezone.make_aware(datetime.combine(dia + timedelta(days=1), time.min))
            for a, b in [(medianoche, seis), (veintidos, siguiente)]:
                total += max(0, (min(fin, b) - max(inicio, a)).total_seconds())
            dia += timedelta(days=1)
    return total


def construir_cuadro_excel(resumen, marcas, tramos, completa, turno, valores, refrigerio_seg):
    base = base_jornada_segundos()
    trabajo = sum((t["fin"] - t["inicio"]).total_seconds() for t in tramos) if completa else None
    saldo = trabajo - base if trabajo is not None and base is not None else None
    extra = max(0, saldo) if saldo is not None else None
    nocturnas = segundos_nocturnos(tramos) if completa else None
    ajustes = list(resumen.ajustes.all())
    feriado_registrado = any(a.concepto == "descanso_feriado" and a.aprobado_el for a in ajustes)
    feriado = formato_tiempo(valores["descanso_feriado"] * Decimal(3600)) if feriado_registrado else "Sin registro"
    totales = {
        "base": formato_tiempo(base), "trabajo": formato_tiempo(trabajo),
        "saldo": formato_tiempo(saldo), "es_deficit": saldo is not None and saldo < 0,
        "he25": formato_tiempo(min(extra, 7200) if extra is not None else None),
        "he35": formato_tiempo(max(extra - 7200, 0) if extra is not None else None),
        "nocturnas": formato_tiempo(nocturnas), "feriado": feriado,
    }
    filas = []
    anterior = None
    for marca in marcas:
        identidad = marca.identidad_biometrica
        codigo = identidad.codigo if identidad else (str(marca.zkteco_user_id) if marca.zkteco_user_id is not None else resumen.persona.dni)
        intervalo = "—"
        if marca.es_valida:
            if anterior:
                intervalo = formato_tiempo((marca.fecha_hora - anterior.fecha_hora).total_seconds())
            anterior = marca
        filas.append({
            "marcacion_id": marca.pk, "evento_codigo": marca.evento_efectivo,
            "es_manual": marca.origen == "SISTEMA_MANUAL",
            "codigo": codigo, "fecha_hora": marca.fecha_local,
            "evento": marca.evento_etiqueta, "valida": marca.es_valida,
            "intervalo": intervalo,
            "es_refrigerio": marca.es_valida and marca.evento_efectivo == "RETORNO_REFRIGERIO",
        })
    incidencias = list(resumen.incidencias.all())
    return {
        "filas": filas, "totales": totales,
        "refrigerio": formato_tiempo(refrigerio_seg) if completa else "Por revisar",
        "descuento": formato_tiempo(valores["descuento"] * Decimal(3600)) if any(a.aprobado_el and a.concepto == "descuento" for a in ajustes) else "Sin registro",
        "compensacion": formato_tiempo(valores["compensacion"] * Decimal(3600)) if any(a.aprobado_el and a.concepto == "compensacion" for a in ajustes) else "Sin registro",
        "incidencias": incidencias,
    }
