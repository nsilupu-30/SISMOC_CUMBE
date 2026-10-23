from calendar import monthrange
from datetime import date
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from asistencia.models import ProgramacionHorario, TurnoHorario, Trabajador
from asistencia.forms_horarios import ProgramarHorarioForm, TurnoConfirmadoForm
from asistencia.services.horarios import programar_horarios
from asistencia.services.revision import puede_gestionar, registrar_historial


@login_required
@require_http_methods(['GET','POST'])
def horarios(request):
    if not puede_gestionar(request.user):
        return HttpResponseForbidden('No tiene permiso para programar horarios.')
    hoy=timezone.localdate()
    try:
        desde=date.fromisoformat(request.GET.get('desde') or hoy.replace(day=1).isoformat())
        hasta=date.fromisoformat(request.GET.get('hasta') or hoy.replace(day=monthrange(hoy.year,hoy.month)[1]).isoformat())
        if hasta<desde or (hasta-desde).days>365: raise ValueError
    except ValueError:
        desde=hoy.replace(day=1); hasta=hoy.replace(day=monthrange(hoy.year,hoy.month)[1])
        messages.error(request,'Revise el rango de fechas. Se muestra el mes actual.')
    trabajador=request.GET.get('trabajador','')
    initial={'desde':desde,'hasta':hasta,'trabajador':trabajador}
    form=ProgramarHorarioForm(initial=initial)
    catalogo=TurnoConfirmadoForm(prefix='nuevo')
    if request.method=='POST':
        if request.POST.get('accion')=='crear_turno':
            catalogo=TurnoConfirmadoForm(request.POST, prefix='nuevo')
            if catalogo.is_valid():
                turno=catalogo.save()
                registrar_historial(None,request.user,'Horario registrado',f'Horario #{turno.pk}: {turno}; tolerancia {turno.tolerancia_minutos} min; refrigerio {turno.hora_inicio_refrigerio} a {turno.hora_fin_refrigerio}.')
                messages.success(request,'Horario registrado. Ahora puede asignarlo a un trabajador.')
                return redirect(request.get_full_path())
        else:
            form=ProgramarHorarioForm(request.POST)
            if form.is_valid():
                data=form.cleaned_data
                try:
                    resultado=programar_horarios(data['trabajador'],data['desde'],data['hasta'],data['dias'],data['turno'],data['motivo'],request.user)
                    messages.success(request,f"{resultado['programadas']} fechas programadas; {resultado['actualizadas']} jornadas actualizadas; {resultado['reagrupadas']} jornadas nocturnas reagrupadas; {resultado['reabiertas']} aprobadas vuelven a revisión; {resultado['sin_cambios']} fechas sin cambios.")
                    return redirect(reverse('programar_horarios')+'?'+urlencode({'desde':data['desde'],'hasta':data['hasta'],'trabajador':data['trabajador'].pk}))
                except ValidationError as exc:
                    form.add_error(None,' '.join(exc.messages))
    qs=ProgramacionHorario.objects.select_related('trabajador','turno','responsable').filter(fecha__range=(desde,hasta))
    if trabajador.isdigit(): qs=qs.filter(trabajador_id=int(trabajador))
    query=urlencode({'desde':desde,'hasta':hasta,'trabajador':trabajador})
    return render(request,'asistencia/horarios.html',{'form':form,'catalogo':catalogo,'mostrar_catalogo':catalogo.is_bound,'programacion':Paginator(qs,50).get_page(request.GET.get('pagina')),'desde':desde,'hasta':hasta,'trabajador_filtro':trabajador,'trabajadores':Trabajador.objects.all(),'turnos':TurnoHorario.objects.filter(activo=True),'query':query})
