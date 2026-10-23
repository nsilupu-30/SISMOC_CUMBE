from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from asistencia.models import Trabajador, IdentidadBiometrica, MarcacionBiometrica, ResumenAsistenciaDiaria, TurnoHorario, CargaArchivoAsistencia, CorreccionEvento, CierreAsistencia, IncidenciaAsistencia, ProgramacionHorario
from asistencia.services.horarios import programar_horarios
from asistencia.services.revision import detalle_jornada
from asistencia.services.revision_trabajador import detalles_en_lote, validar_periodo
from core.models import Usuario


class JornadasNocturnasTests(TestCase):
    def setUp(self):
        self.actor=Usuario.objects.create_user('noche_prueba',email='noche@example.invalid',dni='10101010',rol='CONTADORA')
        self.persona=Trabajador.objects.create(nombre_completo='Persona Nocturna',dni='20202020',area='Operaciones',sede='CHICLAYO')
        self.i=IdentidadBiometrica.objects.create(trabajador=self.persona,sede='CHICLAYO',equipo='1',codigo='100')
        self.turno=TurnoHorario.objects.create(nombre='Nocturno confirmado',hora_entrada=time(20),hora_salida=time(7))
        self.carga=CargaArchivoAsistencia.objects.create(nombre_archivo_original='Prueba agosto.xlsx')
        self.dia=date(2026,8,2)
        self.marcas=[]
        for fecha,hora in [(self.dia,time(21,2,7)),(self.dia,time(23,8,43)),(self.dia,time(23,53,45)),(self.dia+timedelta(days=1),time(7,36,18)),(self.dia+timedelta(days=1),time(19,49))]:
            self.marcas.append(MarcacionBiometrica.objects.create(identidad_biometrica=self.i,fecha_hora=timezone.make_aware(datetime.combine(fecha,hora)),tipo_evento='SIN_CLASIFICAR',carga_origen=self.carga))
        self.r=ResumenAsistenciaDiaria.objects.create(trabajador=self.persona,fecha=self.dia,primera_entrada=time(21,2,7),ultima_salida=time(23,53,45),marcaciones_publicadas=[m.pk for m in self.marcas[:3]])
        self.s=ResumenAsistenciaDiaria.objects.create(trabajador=self.persona,fecha=self.dia+timedelta(days=1),primera_entrada=time(7,36,18),ultima_salida=time(19,49),marcaciones_publicadas=[m.pk for m in self.marcas[3:]])

    def programar(self):
        return programar_horarios(self.persona,self.dia,self.dia,[self.dia.weekday()],self.turno,'Horario confirmado para prueba',self.actor)

    def test_reagrupa_existentes_sin_cambiar_fuentes_ni_otra_entrada(self):
        originales=list(MarcacionBiometrica.objects.values_list('pk','fecha_hora','tipo_evento'))
        result=self.programar();self.r.refresh_from_db();self.s.refresh_from_db()
        self.assertEqual(result['reagrupadas'],1)
        self.assertEqual(self.r.marcaciones_publicadas,[m.pk for m in self.marcas[:4]])
        self.assertEqual(self.s.marcaciones_publicadas,[self.marcas[4].pk])
        self.assertEqual(self.s.primera_entrada,time(19,49))
        self.assertEqual(self.r.ultima_salida,time(7,36,18))
        self.assertFalse(self.r.verificado_contabilidad)
        d=detalle_jornada(self.r)
        self.assertTrue(d['cruza_medianoche'])
        self.assertEqual(len(d['propuestas_eventos']),4)
        self.assertFalse(d['completa'])
        self.assertFalse(CorreccionEvento.objects.exists())
        self.assertEqual(originales,list(MarcacionBiometrica.objects.values_list('pk','fecha_hora','tipo_evento')))
        self.assertEqual(len(detalles_en_lote([self.r,self.s])[0]['marcas']),4)

    def test_confirma_secuencia_calcula_y_no_aprueba(self):
        self.programar();self.r.refresh_from_db()
        propuestas=detalle_jornada(self.r)['propuestas_eventos']
        validar_periodo([self.r],propuestas,{pk:'SIN_CLASIFICAR' for pk in propuestas},None,'Validación de prueba',self.actor)
        self.r.refresh_from_db();d=detalle_jornada(self.r)
        self.assertEqual(d['trabajo_reconstruido'],'09:49:09')
        self.assertEqual(d['refrigerio'],'00:45:02')
        self.assertFalse(self.r.verificado_contabilidad)
        self.assertTrue(d['completa'])

    def test_no_incorpora_marcas_de_otro_archivo(self):
        otra=CargaArchivoAsistencia.objects.create(nombre_archivo_original='Otra carga.xlsx')
        ajena=MarcacionBiometrica.objects.create(identidad_biometrica=self.i,fecha_hora=timezone.make_aware(datetime.combine(self.dia+timedelta(days=1),time(5))),tipo_evento='SIN_CLASIFICAR',carga_origen=otra)
        self.programar();self.r.refresh_from_db()
        self.assertNotIn(ajena.pk,self.r.marcaciones_publicadas)

    def test_cierre_de_manana_revierte_programacion_y_grupos(self):
        CierreAsistencia.objects.create(fecha_inicio=self.s.fecha,fecha_fin=self.s.fecha,total_jornadas=1)
        with self.assertRaises(ValidationError):self.programar()
        self.r.refresh_from_db()
        self.assertEqual(len(self.r.marcaciones_publicadas),3)
        self.assertFalse(ProgramacionHorario.objects.exists())

    def test_incidencias_y_entradas_confirmadas_no_se_mezclan(self):
        IncidenciaAsistencia.objects.create(resumen=self.s,tipo='PERMISO',motivo='Permiso prueba',creado_por=self.actor)
        with self.assertRaises(ValidationError):self.programar()
        self.assertFalse(ProgramacionHorario.objects.exists())

    def test_repetir_no_modifica_una_aprobacion_posterior(self):
        self.programar();self.r.refresh_from_db()
        self.r.verificado_contabilidad=True;self.r.save(update_fields=['verificado_contabilidad'])
        self.programar();self.r.refresh_from_db()
        self.assertTrue(self.r.verificado_contabilidad)

    def test_noches_consecutivas_reagrupan_todo_el_rango_y_no_solo_la_primera(self):
        nuevas=[]
        for offset,hora in [(1,time(23,19,53)),(2,time(0,14,49)),(2,time(7,35,22)),(2,time(19,52,17)),(2,time(23,15,2)),(3,time(0,8,59)),(3,time(7,4,10))]:
            nuevas.append(MarcacionBiometrica.objects.create(identidad_biometrica=self.i,fecha_hora=timezone.make_aware(datetime.combine(self.dia+timedelta(days=offset),hora)),tipo_evento='SIN_CLASIFICAR',carga_origen=self.carga))
        self.s.marcaciones_publicadas.append(nuevas[0].pk);self.s.ultima_salida=time(23,19,53);self.s.save()
        t=ResumenAsistenciaDiaria.objects.create(trabajador=self.persona,fecha=self.dia+timedelta(days=2),primera_entrada=time(0,14,49),ultima_salida=time(23,15,2),marcaciones_publicadas=[m.pk for m in nuevas[1:5]])
        u=ResumenAsistenciaDiaria.objects.create(trabajador=self.persona,fecha=self.dia+timedelta(days=3),primera_entrada=time(0,8,59),ultima_salida=time(7,4,10),marcaciones_publicadas=[m.pk for m in nuevas[5:]])
        programar_horarios(self.persona,self.dia,t.fecha,list(range(7)),self.turno,'Noches confirmadas',self.actor)
        grupos=[]
        for resumen in [self.r,self.s,t]:
            resumen.refresh_from_db();d=detalle_jornada(resumen)
            self.assertEqual(len(d['marcas']),4)
            self.assertEqual(len(d['propuestas_eventos']),4)
            self.assertEqual(d['marcas'][0].fecha_local.date(),resumen.fecha)
            self.assertEqual(d['marcas'][-1].fecha_local.date(),resumen.fecha+timedelta(days=1))
            grupos.extend(m.pk for m in d['marcas'])
        self.assertEqual(len(grupos),len(set(grupos)))
        u.refresh_from_db()
        self.assertEqual(u.marcaciones_publicadas,[])
        self.assertEqual(u.estado,'POR_REVISAR')
        self.assertFalse(u.incidencias.exists())
