from datetime import date, datetime, time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import Usuario
from asistencia.models import Trabajador, IdentidadBiometrica, MarcacionBiometrica, ResumenAsistenciaDiaria, TurnoHorario, CorreccionEvento, CierreAsistencia
from asistencia.services.transferencia import pasar_a_asistencia
from asistencia.services.revision import detalle_jornada
from asistencia.models import IncidenciaAsistencia


class RevisionPorTrabajadorTests(TestCase):
    def setUp(self):
        self.gestor = Usuario.objects.create_user('revisor_persona', email='revisor@example.invalid', dni='11111111', rol='CONTADORA')
        self.ficha = Trabajador.objects.create(nombre_completo='Jorge Aguilar', dni='87654321', area='Boletería', sede='CAJAMARCA')
        self.identidad = IdentidadBiometrica.objects.create(sede='CAJAMARCA', equipo='1', codigo='13', trabajador=self.ficha, nombre=self.ficha.nombre_completo)
        self.desde = date(2026, 8, 1)
        self.hasta = self.desde + timedelta(days=1)
        self.turno = TurnoHorario.objects.create(nombre='Horario revisión', hora_entrada=time(8), hora_salida=time(17), hora_inicio_refrigerio=time(12), hora_fin_refrigerio=time(13))
        for dia in [self.desde, self.hasta]:
            for hora in [time(8), time(12), time(13), time(17)]:
                MarcacionBiometrica.objects.create(identidad_biometrica=self.identidad, fecha_hora=timezone.make_aware(datetime.combine(dia, hora)), tipo_evento='SIN_CLASIFICAR')
        pasar_a_asistencia([self.ficha.pk], self.desde, self.hasta, self.gestor)
        self.client.force_login(self.gestor)
        self.consulta = {'vista': 'asistencia', 'desde': str(self.desde), 'hasta': str(self.hasta)}

    def datos_revision(self):
        datos = {'desde': str(self.desde), 'hasta': str(self.hasta), 'persona_dni': self.ficha.dni, 'turno': self.turno.pk}
        for indice, marca in enumerate(MarcacionBiometrica.objects.filter(identidad_biometrica=self.identidad).order_by('fecha_hora')):
            datos[f'evento_{marca.pk}'] = ['ENTRADA', 'SALIDA_REFRIGERIO', 'RETORNO_REFRIGERIO', 'SALIDA'][indice % 4]
            datos[f'original_{marca.pk}'] = 'SIN_CLASIFICAR'
        return datos

    def test_lista_una_fila_por_trabajador_y_ventana_con_todas_sus_marcas(self):
        respuesta = self.client.get(reverse('dashboard'), self.consulta)
        self.assertEqual(respuesta.context['total_trabajadores_asistencia'], 1)
        self.assertEqual(respuesta.context['pagina_trabajadores'][0]['jornadas'], 2)
        self.assertContains(respuesta, 'Revisar marcaciones')
        self.assertNotContains(respuesta, 'revision-trabajador-dialog')
        respuesta = self.client.get(reverse('dashboard'), {**self.consulta, 'persona_dni': self.ficha.dni})
        self.assertContains(respuesta, 'id="revision-trabajador-dialog"')
        self.assertEqual(len(respuesta.context['revision_trabajador']['marcas']), 8)
        self.assertEqual(len(respuesta.context['revision_trabajador']['detalles']), 2)
        self.assertContains(respuesta, 'Guardar clasificación y validar jornadas')

    def test_clasificar_actualiza_tiempos_sin_aprobar_y_preserva_original(self):
        res = self.client.post(reverse('validar_marcaciones_trabajador'), self.datos_revision())
        self.assertEqual(res.status_code, 302)
        self.assertIn('persona_dni=87654321', res.url)
        self.assertEqual(CorreccionEvento.objects.count(), 8, [str(m) for m in res.wsgi_request._messages])
        for jornada in ResumenAsistenciaDiaria.objects.all():
            self.assertEqual(jornada.horas_trabajadas, 8)
            self.assertEqual(jornada.horas_extras_25, 0)
            self.assertEqual(jornada.estado, 'ASISTIO')
            self.assertFalse(jornada.verificado_contabilidad)
        self.assertFalse(MarcacionBiometrica.objects.exclude(tipo_evento='SIN_CLASIFICAR').exists())
        respuesta = self.client.get(res.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '08:00:00')

    def test_marca_ajena_cancela_todos_los_cambios(self):
        ajena = MarcacionBiometrica.objects.create(usuario=self.gestor, dni=self.gestor.dni, fecha_hora=timezone.make_aware(datetime.combine(self.desde, time(9))))
        datos = self.datos_revision()
        datos[f'evento_{ajena.pk}'] = 'ENTRADA'
        datos[f'original_{ajena.pk}'] = 'SIN_CLASIFICAR'
        self.client.post(reverse('validar_marcaciones_trabajador'), datos)
        self.assertEqual(CorreccionEvento.objects.count(), 0)

    def test_datos_desactualizados_no_sobrescriben_otra_revision(self):
        datos = self.datos_revision()
        marca = MarcacionBiometrica.objects.order_by('fecha_hora').first()
        CorreccionEvento.objects.create(marcacion=marca, tipo_evento='ENTRADA', motivo='Revisión anterior', responsable=self.gestor)
        self.client.post(reverse('validar_marcaciones_trabajador'), datos)
        self.assertEqual(CorreccionEvento.objects.count(), 1)
        self.assertEqual(CorreccionEvento.objects.get().motivo, 'Revisión anterior')

    def test_periodo_cerrado_no_permite_clasificar(self):
        CierreAsistencia.objects.create(fecha_inicio=self.desde, fecha_fin=self.hasta, total_jornadas=2)
        self.client.post(reverse('validar_marcaciones_trabajador'), self.datos_revision())
        self.assertEqual(CorreccionEvento.objects.count(), 0)
        respuesta = self.client.get(reverse('dashboard'), {**self.consulta, 'persona_dni': self.ficha.dni})
        self.assertContains(respuesta, 'Periodo cerrado')

    def test_empleado_no_ve_otra_persona_y_csrf_es_obligatorio(self):
        seguro = Client(enforce_csrf_checks=True)
        seguro.force_login(self.gestor)
        self.assertEqual(seguro.post(reverse('validar_marcaciones_trabajador'), self.datos_revision()).status_code, 403)
        empleado = Usuario.objects.create_user('empleado_sin_revision', email='empleado@example.invalid', dni='22222222', rol='ADMINISTRATIVO')
        self.client.force_login(empleado)
        self.assertEqual(self.client.get(reverse('dashboard'), {**self.consulta, 'persona_dni': self.ficha.dni}).status_code, 404)
        self.assertEqual(self.client.post(reverse('validar_marcaciones_trabajador'), self.datos_revision()).status_code, 403)

    def test_calendario_incluye_fechas_sin_marcas_sin_crear_jornadas(self):
        consulta = {**self.consulta, 'desde': str(self.desde - timedelta(days=1)), 'hasta': str(self.hasta + timedelta(days=1)), 'persona_dni': self.ficha.dni}
        respuesta = self.client.get(reverse('dashboard'), consulta)
        calendario = respuesta.context['revision_trabajador']['calendario']
        self.assertEqual(len(calendario), 4)
        self.assertIsNone(calendario[0]['detalle'])
        self.assertIsNone(calendario[-1]['detalle'])
        self.assertEqual(ResumenAsistenciaDiaria.objects.count(), 2)
        self.assertContains(respuesta, 'Sin marcaciones')
        self.assertContains(respuesta, 'Feriado no laborado')

    def test_registrar_feriado_y_aprobar_sin_inventar_marcas(self):
        dia = self.hasta + timedelta(days=1)
        datos = {'persona_dni': self.ficha.dni, 'desde': str(self.desde), 'hasta': str(dia), 'fecha': str(dia), 'tipo_dia': 'FERIADO_NO_LABORADO'}
        respuesta = self.client.post(reverse('registrar_dia_sin_marcas'), datos)
        self.assertEqual(respuesta.status_code, 302)
        resumen = ResumenAsistenciaDiaria.objects.get(fecha=dia)
        incidencia = IncidenciaAsistencia.objects.get(resumen=resumen)
        self.assertIsNone(incidencia.aprobado_el)
        self.assertFalse(resumen.verificado_contabilidad)
        self.assertEqual(MarcacionBiometrica.objects.count(), 8)
        self.client.post(reverse('accion_jornada', args=[resumen.pk]), {'accion': 'aprobar_incidencia', 'registro_id': incidencia.pk})
        resumen.refresh_from_db()
        self.assertEqual(resumen.estado, 'FERIADO')
        self.assertEqual(detalle_jornada(resumen)['bloqueos'], [])
        self.assertEqual(resumen.horas_trabajadas, 0)

    def test_no_registrar_descanso_sobre_dia_con_marcas_o_cerrado(self):
        datos = {'persona_dni': self.ficha.dni, 'desde': str(self.desde), 'hasta': str(self.hasta + timedelta(days=1)), 'fecha': str(self.desde), 'tipo_dia': 'DESCANSO_SEMANAL'}
        self.client.post(reverse('registrar_dia_sin_marcas'), datos)
        self.assertEqual(IncidenciaAsistencia.objects.count(), 0)
        dia = self.hasta + timedelta(days=1)
        CierreAsistencia.objects.create(fecha_inicio=dia, fecha_fin=dia, total_jornadas=0)
        self.client.post(reverse('registrar_dia_sin_marcas'), {**datos, 'fecha': str(dia)})
        self.assertEqual(ResumenAsistenciaDiaria.objects.count(), 2)
        self.assertEqual(IncidenciaAsistencia.objects.count(), 0)

    def test_descanso_pendiente_muestra_situacion_sin_detalle_de_marcas(self):
        dia = self.hasta + timedelta(days=1)
        datos = {'persona_dni': self.ficha.dni, 'desde': str(self.desde), 'hasta': str(dia), 'fecha': str(dia), 'tipo_dia': 'DESCANSO_SEMANAL'}
        respuesta = self.client.post(reverse('registrar_dia_sin_marcas'), datos)
        self.assertNotIn('detalle=', respuesta.url)
        resumen = ResumenAsistenciaDiaria.objects.get(fecha=dia)
        detalle = detalle_jornada(resumen)
        self.assertTrue(detalle['solo_situacion'])
        self.assertNotIn('Trabajador sin turno asignado.', detalle['alertas'])
        self.assertEqual(detalle['bloqueos'], ['Apruebe la situación del día registrada.'])
        respuesta = self.client.get(reverse('dashboard'), {**self.consulta, 'hasta': str(dia), 'persona_dni': self.ficha.dni, 'detalle': resumen.pk})
        self.assertIsNone(respuesta.context['detalle_jornada'])
        self.assertNotContains(respuesta, 'id="detalle-jornada-dialog"')
        self.assertContains(respuesta, 'Aprobar situación')
        self.assertContains(respuesta, 'class="dia-no-laborado"')

    def test_aprobar_descanso_y_dia_desde_la_fila(self):
        dia = self.hasta + timedelta(days=1)
        self.client.post(reverse('registrar_dia_sin_marcas'), {'persona_dni': self.ficha.dni, 'desde': str(self.desde), 'hasta': str(dia), 'fecha': str(dia), 'tipo_dia': 'DESCANSO_SEMANAL'})
        resumen = ResumenAsistenciaDiaria.objects.get(fecha=dia)
        incidencia = IncidenciaAsistencia.objects.get(resumen=resumen)
        datos = {'persona_dni': self.ficha.dni, 'desde': str(self.desde), 'hasta': str(dia), 'solo_situacion': 'si'}
        respuesta = self.client.post(reverse('accion_jornada', args=[resumen.pk]), {**datos, 'accion': 'aprobar_incidencia', 'registro_id': incidencia.pk})
        self.assertNotIn('detalle=', respuesta.url)
        self.client.post(reverse('accion_jornada', args=[resumen.pk]), {**datos, 'accion': 'APROBADO'})
        resumen.refresh_from_db()
        self.assertTrue(resumen.verificado_contabilidad)
        self.assertEqual(resumen.estado, 'DIA_LIBRE')
        self.assertEqual(MarcacionBiometrica.objects.count(), 8)

    def test_incidente_no_oculta_marcas_de_una_jornada_laborada(self):
        resumen = ResumenAsistenciaDiaria.objects.order_by('fecha').first()
        IncidenciaAsistencia.objects.create(resumen=resumen, tipo='DESCANSO_SEMANAL', motivo='Revisar situación', creado_por=self.gestor)
        self.assertFalse(detalle_jornada(resumen)['solo_situacion'])
