import csv
import json
from datetime import date
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Usuario
from asistencia.models import (
    ResumenAsistenciaDiaria, MarcacionBiometrica, TurnoHorario, CargaArchivoAsistencia,
    IncidenciaAsistencia, AjusteAsistencia, CorreccionEvento, CierreAsistencia,
)
from asistencia.services.revision import (
    puede_gestionar, puede_aprobar, comprobar_abierto, detalle_jornada,
    valores_ajustados, estado_revision, registrar_historial, dejar_pendiente, revisar,
)


def queryset_visible(usuario):
    qs = ResumenAsistenciaDiaria.objects.select_related("usuario__turno", "turno_aplicado", "revisado_por").prefetch_related("incidencias", "ajustes")
    return qs if puede_gestionar(usuario) else qs.filter(usuario=usuario)


def filtros_asistencia(request):
    hoy = timezone.localdate()
    error = ""
    try:
        inicio = date.fromisoformat(request.GET.get("desde") or hoy.replace(day=1).isoformat())
        fin = date.fromisoformat(request.GET.get("hasta") or hoy.isoformat())
        if fin < inicio:
            raise ValueError
    except ValueError:
        inicio, fin = hoy.replace(day=1), hoy
        error = "El intervalo de fechas no es válido. Se muestra el mes actual."
    return {
        "desde": inicio.isoformat(), "hasta": fin.isoformat(), "sede": request.GET.get("sede", ""),
        "trabajador": request.GET.get("trabajador", "").strip(), "estado": request.GET.get("estado", ""),
        "revision": request.GET.get("revision", ""), "error": error,
    }


def reporte_filtrado(request):
    f = filtros_asistencia(request)
    qs = queryset_visible(request.user).filter(fecha__range=(f["desde"], f["hasta"]))
    if f["sede"]:
        qs = qs.filter(usuario__agencia_sede=f["sede"])
    if f["trabajador"]:
        term = f["trabajador"]
        for palabra in term.split():
            qs = qs.filter(Q(usuario__dni__icontains=palabra) | Q(usuario__first_name__icontains=palabra) | Q(usuario__last_name__icontains=palabra))
    if f["estado"]:
        qs = qs.filter(estado=f["estado"])
    if f["revision"] == "APROBADO":
        qs = qs.filter(verificado_contabilidad=True)
    elif f["revision"] in {"PENDIENTE", "OBSERVADO"}:
        qs = qs.filter(verificado_contabilidad=False, estado_revision=f["revision"])
    return f, qs.order_by("-fecha", "usuario__last_name", "pk")


def consolidar(resumenes):
    personas = {}
    for r in resumenes:
        fila = personas.setdefault(r.usuario_id, {
            "usuario": r.usuario, "jornadas": 0, "aprobadas": 0, "pendientes": 0,
            "observadas": 0, "tardanza": 0, "ajustes": 0,
            **{k: Decimal(0) for k, _ in AjusteAsistencia.CONCEPTOS},
        })
        fila["jornadas"] += 1
        revision = estado_revision(r)
        fila[{"APROBADO": "aprobadas", "OBSERVADO": "observadas", "PENDIENTE": "pendientes"}[revision]] += 1
        fila["tardanza"] += r.minutos_tardanza
        fila["ajustes"] += len(r.ajustes.all())
        for key, val in valores_ajustados(r).items():
            fila[key] += val
    return list(personas.values())


def contexto_asistencia(request):
    filtros, qs = reporte_filtrado(request)
    resumenes = list(qs)
    conteos = {s: 0 for s in ("APROBADO", "PENDIENTE", "OBSERVADO")}
    for r in resumenes:
        r.revision_visible = estado_revision(r)
        r.turno_visible = r.turno_aplicado or r.usuario.turno
        r.valores = valores_ajustados(r)
        conteos[r.revision_visible] += 1
    pagina = Paginator(resumenes, 30).get_page(request.GET.get("pagina"))
    # Solo reconstruir las jornadas de la página, no todo el histórico.
    for r in pagina:
        d = detalle_jornada(r)
        r.refrigerio_visible = d["refrigerio"] or "Por revisar"
        r.alertas = d["alertas"]
        r.completa = d["completa"]
        r.deficit_visible = d["deficit_minutos"]
    visibles = Usuario.objects.all() if puede_gestionar(request.user) else Usuario.objects.filter(pk=request.user.pk)
    query = {k: v for k, v in filtros.items() if k != "error" and v}
    query["vista"] = "asistencia"
    detalle = None
    if request.GET.get("detalle", "").isdigit():
        r = get_object_or_404(queryset_visible(request.user), pk=int(request.GET["detalle"]))
        detalle = detalle_jornada(r)
    inicio, fin = filtros["desde"], filtros["hasta"]
    marcas = MarcacionBiometrica.objects.filter(fecha_hora__date__range=(inicio, fin))
    if not puede_gestionar(request.user):
        marcas = marcas.filter(usuario=request.user)
    sin_identidad = marcas.filter(usuario__isnull=True).order_by("fecha_hora")
    if filtros["sede"] or filtros["trabajador"]:
        # Las marcas sin identidad aún no tienen una sede o trabajador confiables.
        sin_identidad_visible = []
    else:
        sin_identidad_visible = list(sin_identidad[:30])
    totales = {k: sum((r.valores[k] for r in resumenes), Decimal(0)) for k, _ in AjusteAsistencia.CONCEPTOS}
    return {
        "filtros": filtros, "pagina_asistencia": pagina, "consulta_asistencia": urlencode(query),
        "detalle_jornada": detalle, "consolidado": consolidar(resumenes), "conteos_revision": conteos,
        "total_jornadas": len(resumenes), "totales_asistencia": totales,
        "total_vueltas": sum(r.total_vueltas_num for r in resumenes),
        "sedes_asistencia": list(visibles.order_by("agencia_sede").values_list("agencia_sede", flat=True).distinct()),
        "estados_asistencia": ResumenAsistenciaDiaria.EstadoAsistencia.choices,
        "tipos_incidencia": IncidenciaAsistencia.TIPOS, "conceptos_ajuste": AjusteAsistencia.CONCEPTOS,
        "tipos_evento": MarcacionBiometrica.TipoEvento.choices,
        "puede_gestionar": puede_gestionar(request.user), "puede_aprobar": puede_aprobar(request.user),
        "sin_identidad": sin_identidad_visible, "total_sin_identidad": sin_identidad.count(),
        "usuarios_asistencia": visibles.filter(esta_activo=True, is_active=True),
        "cargas_con_error": CargaArchivoAsistencia.objects.filter(estado="ERROR").order_by("-fecha_subida")[:10] if puede_gestionar(request.user) else [],
        "cierres_asistencia": CierreAsistencia.objects.filter(fecha_inicio__lte=fin, fecha_fin__gte=inicio) if puede_gestionar(request.user) else [],
        "jornadas_fecha_futura": queryset_visible(request.user).filter(fecha__gt=timezone.localdate()).count(),
    }


def volver(request, resumen_id=None):
    # Construir la redirección con parámetros conocidos; no aceptar URLs externas.
    parametros = {k: request.POST[k] for k in ("desde", "hasta", "sede", "trabajador", "estado", "revision") if request.POST.get(k)}
    parametros["vista"] = "asistencia"
    if resumen_id:
        parametros["detalle"] = resumen_id
    return redirect(reverse("dashboard") + "?" + urlencode(parametros))


@login_required
@require_POST
def accion_jornada(request, resumen_id):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden("No tiene permiso para gestionar asistencia.")
    try:
        with transaction.atomic():
            r = get_object_or_404(queryset_visible(request.user).select_for_update(of=('self',)), pk=resumen_id)
            comprobar_abierto(r.fecha)
            accion = request.POST.get("accion")
            motivo = request.POST.get("motivo", "").strip()
            if accion in {"APROBADO", "OBSERVADO"}:
                revisar(r, request.user, accion, motivo)
            elif accion == "turno":
                turno = get_object_or_404(TurnoHorario, pk=request.POST.get("turno"), activo=True)
                r.turno_aplicado = turno
                r.save(update_fields=["turno_aplicado"])
                dejar_pendiente(r, request.user, f"Turno de la jornada: {turno.nombre}")
            elif accion == "incidencia":
                if not motivo:
                    raise ValidationError("Indique el motivo de la incidencia.")
                incidencia = IncidenciaAsistencia(
                    resumen=r, tipo=request.POST.get("tipo"), motivo=motivo,
                    minutos=request.POST.get("minutos") or None,
                    evidencia_url=request.POST.get("evidencia_url", "").strip(), creado_por=request.user,
                )
                incidencia.full_clean()
                incidencia.save()
                dejar_pendiente(r, request.user, "Incidencia registrada: " + incidencia.get_tipo_display())
            elif accion == "ajuste":
                if not motivo:
                    raise ValidationError("Indique el motivo del ajuste.")
                minutos = int(request.POST.get("minutos", "0"))
                if minutos == 0:
                    raise ValidationError("El ajuste debe tener una duración distinta de cero.")
                ajuste = AjusteAsistencia(
                    resumen=r, concepto=request.POST.get("concepto"), minutos=minutos,
                    motivo=motivo, fecha_origen=request.POST.get("fecha_origen") or None, creado_por=request.user,
                )
                ajuste.full_clean()
                ajuste.save()
                dejar_pendiente(r, request.user, f"Ajuste propuesto: {ajuste.get_concepto_display()}, {minutos} minutos. {motivo}")
            elif accion in {"aprobar_incidencia", "aprobar_ajuste"}:
                if not puede_aprobar(request.user):
                    return HttpResponseForbidden("La aprobación corresponde a Contabilidad o Gerencia.")
                model = IncidenciaAsistencia if accion == "aprobar_incidencia" else AjusteAsistencia
                obj = get_object_or_404(model, pk=request.POST.get("registro_id"), resumen=r, aprobado_el__isnull=True)
                if accion == "aprobar_ajuste":
                    nuevo_total = valores_ajustados(r)[obj.concepto] + Decimal(obj.minutos) / Decimal(60)
                    if nuevo_total < 0:
                        raise ValidationError("El ajuste dejaría el concepto con un total negativo. Registre una propuesta corregida.")
                elif obj.tipo == "VACACIONES" and obj.minutos is None and r.horas_trabajadas > 0:
                    raise ValidationError("La jornada tiene horas trabajadas. Concilie ese tiempo antes de aprobar vacaciones de día completo.")
                obj.aprobado_por, obj.aprobado_el = request.user, timezone.now()
                obj.save(update_fields=["aprobado_por", "aprobado_el"])
                if accion == "aprobar_incidencia" and obj.minutos is None:
                    estados = {"VACACIONES": "VACACIONES", "PERMISO": "PERMISO", "DESCANSO_MEDICO": "DESCANSO_MEDICO", "CAMBIO_DESCANSO": "DIA_LIBRE"}
                    if obj.tipo in estados:
                        r.estado = estados[obj.tipo]
                        r.save(update_fields=["estado"])
                dejar_pendiente(r, request.user, f"{obj.__class__.__name__} #{obj.pk} aprobado: {obj.motivo}")
            elif accion == "corregir_evento":
                if not motivo:
                    raise ValidationError("Indique por qué corrige el tipo de marcación.")
                marca = get_object_or_404(MarcacionBiometrica, pk=request.POST.get("marcacion_id"), usuario=r.usuario)
                if marca.pk not in [m.pk for m in detalle_jornada(r)["marcas"]]:
                    raise ValidationError("La marcación no pertenece al intervalo de esta jornada.")
                evento = request.POST.get("tipo_evento")
                if evento not in MarcacionBiometrica.TipoEvento.values:
                    raise ValidationError("Tipo de evento no válido.")
                CorreccionEvento.objects.update_or_create(marcacion=marca, defaults={"tipo_evento": evento, "motivo": motivo, "responsable": request.user})
                dejar_pendiente(r, request.user, "Se registró una corrección de evento.")
                registrar_historial(r, request.user, "Tipo de evento corregido", f"Original: {marca.tipo_evento}; efectivo: {evento}. {motivo}", marca)
            else:
                raise ValidationError("Acción no válida.")
        messages.success(request, "Cambio guardado. Consulte el detalle y el historial de la jornada.")
    except (ValidationError, ValueError, TypeError) as exc:
        messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else "Revise los campos del formulario.")
    return volver(request, resumen_id)


@login_required
@require_POST
def asociar_marcacion(request, marcacion_id):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden("No tiene permiso para asociar marcaciones.")
    try:
        with transaction.atomic():
            marca = get_object_or_404(MarcacionBiometrica.objects.select_for_update(), pk=marcacion_id, usuario__isnull=True)
            comprobar_abierto(timezone.localtime(marca.fecha_hora).date())
            usuario = get_object_or_404(Usuario, pk=request.POST.get("usuario"), esta_activo=True, is_active=True)
            motivo = request.POST.get("motivo", "").strip()
            if not motivo:
                raise ValidationError("Indique el motivo de la asociación.")
            marca.usuario = usuario
            marca.save(update_fields=["usuario"])
            registrar_historial(None, request.user, "Identidad asociada", f"Trabajador #{usuario.pk}. {motivo}", marca)
        messages.success(request, "Identidad asociada. La marca original conserva su DNI e identificador reportados.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    return volver(request)


@login_required
def exportar_asistencia(request):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden("No tiene permiso para exportar el resumen contable.")
    f, qs = reporte_filtrado(request)
    if f["error"]:
        return HttpResponse(f["error"], status=400)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="asistencia_{f["desde"]}_{f["hasta"]}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Desde", "Hasta", "DNI", "Trabajador", "Sede", "Jornadas", "Aprobadas", "Pendientes", "Observadas", "Horas efectivas", "Extras 25 %", "Extras 35 %", "Nocturnas", "Descanso/feriado", "Descuento (h)", "Compensacion (h)"])
    for fila in consolidar(qs):
        u = fila["usuario"]
        def seguro(value):
            text = str(value)
            return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
        writer.writerow([f["desde"], f["hasta"], seguro(u.dni), seguro(u.nombre_completo), seguro(u.agencia_sede), fila["jornadas"], fila["aprobadas"], fila["pendientes"], fila["observadas"], *[f"{fila[k]:.2f}" for k, _ in AjusteAsistencia.CONCEPTOS]])
    return response


@login_required
@require_POST
def cerrar_periodo(request):
    if not puede_aprobar(request.user):
        return HttpResponseForbidden("Solo Contabilidad o Gerencia puede cerrar periodos.")
    try:
        if request.POST.get("confirmar") != "si":
            raise ValidationError("Confirme que ha revisado el periodo completo antes de cerrarlo.")
        inicio, fin = date.fromisoformat(request.POST.get("desde", "")), date.fromisoformat(request.POST.get("hasta", ""))
        if fin < inicio or fin >= timezone.localdate():
            raise ValidationError("El periodo debe terminar antes de hoy y tener fechas en orden.")
        with transaction.atomic():
            if CierreAsistencia.objects.filter(fecha_inicio__lte=fin, fecha_fin__gte=inicio).exists():
                raise ValidationError("El intervalo se superpone con un periodo cerrado.")
            qs = list(queryset_visible(request.user).select_for_update(of=('self',)).filter(fecha__range=(inicio, fin)))
            if not qs or any(estado_revision(r) != "APROBADO" for r in qs):
                raise ValidationError("Debe haber jornadas y todas deben estar aprobadas para cerrar el periodo completo.")
            if MarcacionBiometrica.objects.filter(fecha_hora__date__range=(inicio, fin), usuario__isnull=True).exists():
                raise ValidationError("Hay marcaciones sin trabajador asociado en el periodo.")
            if any(detalle_jornada(r)["bloqueos"] for r in qs):
                raise ValidationError("Hay jornadas con incidencias de cálculo sin resolver.")
            sin_resumen = MarcacionBiometrica.objects.filter(fecha_hora__date__range=(inicio, fin), es_valida=True)
            for marca in sin_resumen.select_related("usuario"):
                dia = timezone.localtime(marca.fecha_hora).date()
                if not any(r.usuario_id == marca.usuario_id and detalle_jornada_intervalo_contiene(r, marca.fecha_hora) for r in qs):
                    raise ValidationError("Hay marcaciones del periodo sin una jornada revisada que las incluya.")
            snapshot = [{**{k: str(v) for k, v in valores_ajustados(r).items()}, "resumen_id": r.pk, "dni": r.usuario.dni, "fecha": r.fecha.isoformat()} for r in qs]
            cierre = CierreAsistencia.objects.create(fecha_inicio=inicio, fecha_fin=fin, cerrado_por=request.user, total_jornadas=len(qs), resumen_cierre=snapshot)
            registrar_historial(None, request.user, "Periodo cerrado", f"Cierre #{cierre.pk}: {inicio} a {fin}; {len(qs)} jornadas.")
        messages.success(request, "Periodo completo cerrado. Se guardó una copia de sus resultados aprobados.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else "Las fechas del cierre no son válidas.")
    return volver(request)


def detalle_jornada_intervalo_contiene(resumen, fecha_hora):
    from asistencia.services.revision import ventana_jornada
    inicio, fin = ventana_jornada(resumen)
    return inicio <= fecha_hora <= fin


@login_required
@require_POST
def crear_jornada(request):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden("No tiene permiso para crear jornadas.")
    resumen = None
    try:
        with transaction.atomic():
            fecha = date.fromisoformat(request.POST.get("fecha", ""))
            comprobar_abierto(fecha)
            usuario = get_object_or_404(Usuario, pk=request.POST.get("usuario"), esta_activo=True)
            resumen, nueva = ResumenAsistenciaDiaria.objects.get_or_create(usuario=usuario, fecha=fecha, defaults={"estado": "PERMISO", "turno_aplicado": usuario.turno})
            if nueva:
                registrar_historial(resumen, request.user, "Jornada creada", "Sin marcas ni horas; pendiente de documentar y revisar.")
                messages.success(request, "Jornada creada. Agregue la incidencia o revise las marcaciones.")
            else:
                messages.info(request, "La jornada ya existe. Se muestra su detalle.")
    except (ValueError, ValidationError) as exc:
        messages.error(request, " ".join(exc.messages) if isinstance(exc, ValidationError) else "Seleccione una fecha válida.")
    return volver(request, resumen.pk if resumen else None)


@login_required
@require_POST
def consultar_huellero(request):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden("No tiene permiso para consultar el equipo.")
    from asistencia.services.zkteco_live import ZKTecoLiveClient
    return JsonResponse(ZKTecoLiveClient().sincronizar_marcaciones_en_vivo())


@login_required
@require_POST
def importar_excel_web(request):
    if not puede_gestionar(request.user):
        return JsonResponse({"detail": "No tiene permiso para importar archivos."}, status=403)
    archivo = request.FILES.get("file")
    if not archivo or not archivo.name.lower().endswith((".xlsx", ".xls")):
        return JsonResponse({"detail": "Seleccione un archivo Excel .xlsx o .xls."}, status=400)
    from asistencia.services.zkteco_parser import ZKTecoExcelParser
    try:
        with transaction.atomic():
            resultado = ZKTecoExcelParser(archivo, archivo.name, request.user).procesar()
        return JsonResponse(resultado)
    except ValidationError as exc:
        return JsonResponse({"detail": " ".join(exc.messages)}, status=400)
    except Exception:
        return JsonResponse({"detail": "No se pudo importar el archivo. Revise el formato y los identificadores antes de reintentar."}, status=400)


@login_required
@require_POST
def marcar_web(request):
    from asistencia.api import registrar_marcacion
    from asistencia.schemas import MarcacionCreateSchema
    from ninja.errors import HttpError
    from pydantic import ValidationError as SchemaError
    if not request.user.esta_activo or not request.user.is_active:
        return JsonResponse({"detail": "La cuenta está inactiva."}, status=403)
    try:
        data = MarcacionCreateSchema(**json.loads(request.body))
        if data.origen != "KIOSKO_PIN":
            return JsonResponse({"detail": "El registro web debe indicar origen Kiosko (DNI)."}, status=400)
        request.auth = request.user
        with transaction.atomic():
            marca = registrar_marcacion(request, data)
        return JsonResponse({"id": marca.pk, "mensaje": "Marcación registrada. La jornada queda pendiente de revisión."})
    except HttpError as exc:
        return JsonResponse({"detail": str(exc)}, status=exc.status_code)
    except ValidationError as exc:
        return JsonResponse({"detail": " ".join(exc.messages)}, status=400)
    except (SchemaError, ValueError, TypeError):
        return JsonResponse({"detail": "Revise el DNI y el tipo de marcación."}, status=400)
