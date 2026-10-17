from datetime import date, datetime, time
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import Usuario
from asistencia.models import Trabajador, IdentidadBiometrica, MarcacionBiometrica, ResumenAsistenciaDiaria, TurnoHorario, CierreAsistencia, CorreccionEvento
from asistencia.services.revision import detalle_jornada


class MarcacionManualTests(TestCase):
    def setUp(self):
        self.contadora = Usuario.objects.create_user('contadora_manual', email='contadora@example.invalid', dni='11111111', rol='CONTADORA')
        self.ficha = Trabajador.objects.create(nombre_completo='Abisag Salazar', dni='87654328', area='Boletería', sede='CAJAMARCA')
        self.identidad = IdentidadBiometrica.objects.create(sede='CAJAMARCA', equipo='1', codigo='42', trabajador=self.ficha)
        self.dia = date(2026, 8, 22)
        turno = TurnoHorario.objects.create(nombre='Mañana Cajamarca', hora_entrada=time(6), hora_salida=time(15))
        self.resumen = ResumenAsistenciaDiaria.objects.create(trabajador=self.ficha, fecha=self.dia, primera_entrada=time(6, 4, 29), ultima_salida=time(14, 47, 14), turno_aplicado=turno, estado='POR_REVISAR')
        self.marcas = []
        for hora, tipo in [(time(6, 4, 29), 'ENTRADA'), (time(8, 21, 37), 'SALIDA_REFRIGERIO'), (time(14, 47, 14), 'RETORNO_REFRIGERIO')]:
            self.marcas.append(MarcacionBiometrica.objects.create(identidad_biometrica=self.identidad, fecha_hora=timezone.make_aware(datetime.combine(self.dia, hora)), tipo_evento=tipo, origen='EXCEL_ZKTECO'))
        self.url = reverse('accion_jornada', args=[self.resumen.pk])
        self.datos = {'accion': 'marcacion_manual', 'fecha_manual': str(self.dia), 'hora_manual': '09:05:00', 'tipo_evento_manual': 'RETORNO_REFRIGERIO', 'identidad_manual': self.identidad.pk, 'motivo_manual': 'Retorno confirmado con el control de la contadora', 'evidencia_manual_url': 'https://example.invalid/control'}
        self.client.force_login(self.contadora)

    def test_agregar_faltante_y_guardar_clasificacion_sin_alterar_originales(self):
        ultima = self.marcas[-1]
        datos = {**self.datos, f'evento_{ultima.pk}': 'SALIDA', f'original_{ultima.pk}': 'RETORNO_REFRIGERIO'}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 302)
        manual = MarcacionBiometrica.objects.get(origen='SISTEMA_MANUAL')
        self.assertEqual(manual.registrada_por, self.contadora)
        self.assertEqual(manual.identidad_biometrica, self.identidad)
        self.assertIsNone(manual.carga_origen_id)
        self.assertEqual(manual.verificacion_reportada, '')
        self.assertEqual(manual.motivo_manual, self.datos['motivo_manual'])
        self.assertEqual(Usuario.objects.count(), 1)
        for original in self.marcas:
            original.refresh_from_db()
            self.assertEqual(original.origen, 'EXCEL_ZKTECO')
        ultima.refresh_from_db()
        self.assertEqual(ultima.tipo_evento, 'RETORNO_REFRIGERIO')
        self.resumen.refresh_from_db()
        detalle = detalle_jornada(self.resumen)
        self.assertTrue(detalle['completa'])
        self.assertEqual(detalle['trabajo_reconstruido'], '07:59:22')
        self.assertEqual(detalle['refrigerio'], '00:43:23')
        self.assertEqual(self.resumen.horas_trabajadas, Decimal('7.99'))
        self.assertFalse(self.resumen.verificado_contabilidad)
        self.assertTrue(self.resumen.historial_revision.filter(accion='Marcación manual agregada').exists())
        respuesta = self.client.get(reverse('dashboard'), {'vista': 'asistencia', 'desde': str(self.dia), 'hasta': str(self.dia), 'detalle': self.resumen.pk})
        self.assertContains(respuesta, 'Registro manual')
        self.assertContains(respuesta, 'Agregar marcación manual')

    def test_no_repetir_ni_registrar_hora_ajena_a_la_jornada(self):
        self.client.post(self.url, self.datos)
        self.client.post(self.url, self.datos)
        self.assertEqual(MarcacionBiometrica.objects.filter(origen='SISTEMA_MANUAL').count(), 1)
        self.client.post(self.url, {**self.datos, 'fecha_manual': '2026-08-25'})
        self.assertEqual(MarcacionBiometrica.objects.count(), 4)

    def test_dato_manual_invalido_revierte_correcciones_del_mismo_envio(self):
        ultima = self.marcas[-1]
        self.client.post(self.url, {**self.datos, 'motivo_manual': '', f'evento_{ultima.pk}': 'SALIDA', f'original_{ultima.pk}': 'RETORNO_REFRIGERIO'})
        self.assertFalse(CorreccionEvento.objects.exists())
        self.assertEqual(MarcacionBiometrica.objects.count(), 3)

    def test_no_aceptar_codigo_de_otro_trabajador(self):
        otra = IdentidadBiometrica.objects.create(sede='TRUJILLO', equipo='1', codigo='42')
        self.client.post(self.url, {**self.datos, 'identidad_manual': otra.pk})
        self.assertEqual(MarcacionBiometrica.objects.count(), 3)

    def test_entrada_o_salida_faltante_amplia_intervalo_guardado(self):
        self.client.post(self.url, {**self.datos, 'hora_manual': '15:00:00', 'tipo_evento_manual': 'SALIDA'})
        self.resumen.refresh_from_db()
        self.assertEqual(self.resumen.ultima_salida, time(15))
        self.assertEqual(len(detalle_jornada(self.resumen)['marcas']), 4)

    def test_respeta_cierre_permisos_y_csrf(self):
        seguro = Client(enforce_csrf_checks=True)
        seguro.force_login(self.contadora)
        self.assertEqual(seguro.post(self.url, self.datos).status_code, 403)
        CierreAsistencia.objects.create(fecha_inicio=self.dia, fecha_fin=self.dia, total_jornadas=1)
        self.client.post(self.url, self.datos)
        self.assertEqual(MarcacionBiometrica.objects.count(), 3)
        self.contadora.rol = 'ADMINISTRATIVO'
        self.contadora.save()
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 403)
