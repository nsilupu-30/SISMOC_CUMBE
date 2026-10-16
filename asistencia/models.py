# ==============================================================================
# asistencia/models.py
# SISMOC-CUMBE | Modelos para Gestión de Asistencia, Biometría ZKTeco y Planillas
# Empresa de Transportes El Cumbe S.A.C. — RUC: 20480397731
# ==============================================================================

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TurnoHorario(models.Model):
    """Horarios y turnos de trabajo configurados para agencias y oficinas."""
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Turno")
    hora_entrada = models.TimeField(verbose_name="Hora Oficial de Entrada")
    hora_salida = models.TimeField(verbose_name="Hora Oficial de Salida")
    tolerancia_minutos = models.PositiveIntegerField(
        default=15,
        verbose_name="Tolerancia de Tardanza (minutos)",
        help_text="Minutos de gracia permitidos antes de computar tardanza",
    )
    hora_inicio_refrigerio = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Inicio de Refrigerio",
    )
    hora_fin_refrigerio = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Fin de Refrigerio",
    )
    es_para_conductores = models.BooleanField(
        default=False,
        verbose_name="Turno Operativo de Conductores",
        help_text="Para conductores el cálculo se rige por Vueltas Simples/Dobles y SUTRAN 8h",
    )
    activo = models.BooleanField(default=True, verbose_name="Turno Activo")

    class Meta:
        verbose_name = "Turno y Horario Laboral"
        verbose_name_plural = "Turnos y Horarios Laborales"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.hora_entrada.strftime('%H:%M')} - {self.hora_salida.strftime('%H:%M')})"


class MarcacionBiometrica(models.Model):
    """
    Registro atómico de marcación biométrica (huella dactilar, reconocimiento facial o app móvil).
    Captura eventos desde:
    1. Reloj Biométrico ZKTeco físico conectado por TCP/IP en tiempo real.
    2. Archivos Excel/DAT exportados del ZKSoftware (`ASISTENCIA AGOSTO 2026.xlsx`).
    3. App Móvil con Reconocimiento Facial + Geofencing GPS en carretera.
    """

    class TipoEvento(models.TextChoices):
        ENTRADA = "ENTRADA", _("🟢 Entrada a Laborar")
        SALIDA = "SALIDA", _("🔴 Salida de Laborar")
        SALIDA_REFRIGERIO = "SALIDA_REFRIGERIO", _("☕ Salida a Refrigerio")
        RETORNO_REFRIGERIO = "RETORNO_REFRIGERIO", _("🍽️ Retorno de Refrigerio")

    class OrigenMarcacion(models.TextChoices):
        ZKTECO_EN_LINEA = "ZKTECO_EN_LINEA", _("⚡ ZKTeco Biométrico (Tiempo Real)")
        EXCEL_ZKTECO = "EXCEL_ZKTECO", _("📂 Archivo Excel ZKTeco (Batch)")
        APP_MOVIL_GPS = "APP_MOVIL_GPS", _("📱 App Móvil (Facial + GPS)")
        KIOSKO_PIN = "KIOSKO_PIN", _("🖥️ Kiosko de Terminal (PIN/DNI)")

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marcaciones",
        verbose_name="Colaborador",
    )
    dni = models.CharField(
        max_length=8,
        db_index=True,
        verbose_name="DNI del Trabajador",
    )
    nombre_empleado = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Nombre Reportado en Marcación",
    )
    zkteco_user_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="ID de Usuario en Reloj ZKTeco",
    )
    fecha_hora = models.DateTimeField(
        db_index=True,
        verbose_name="Fecha y Hora de la Marcación",
    )
    tipo_evento = models.CharField(
        max_length=20,
        choices=TipoEvento.choices,
        default=TipoEvento.ENTRADA,
        verbose_name="Tipo de Evento",
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenMarcacion.choices,
        default=OrigenMarcacion.ZKTECO_EN_LINEA,
        verbose_name="Canal de Marcación",
    )
    dispositivo_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP del Dispositivo ZKTeco",
    )
    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Latitud GPS (App Móvil)",
    )
    longitud = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name="Longitud GPS (App Móvil)",
    )
    foto_evidencia = models.ImageField(
        upload_to="asistencia/fotos_marcaciones/",
        null=True,
        blank=True,
        verbose_name="Foto de Marcación Facial",
    )
    es_valida = models.BooleanField(
        default=True,
        verbose_name="Marcación Válida",
    )
    fecha_registro_sistema = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro en Servidor",
    )

    class Meta:
        verbose_name = "Marcación Biométrica"
        verbose_name_plural = "Marcaciones Biométricas (Logs ZKTeco / App)"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["dni", "fecha_hora"]),
            models.Index(fields=["fecha_hora"]),
        ]

    def __str__(self):
        return f"{self.dni} | {self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')} | {self.get_tipo_evento_display()}"


class ResumenAsistenciaDiaria(models.Model):
    """
    Consolidado diario por trabajador calculado automáticamente mediante el algoritmo
    diseñado para Transportes El Cumbe S.A.C.:
    - Administrativos: Tardanza, Horas Extras 25%, 35% y Nocturnas (22:00 a 06:00).
    - Conductores: Vueltas Simples ('X'=1), Vueltas Dobles ('XX'=2), Descanso SUTRAN.
    """

    class EstadoAsistencia(models.TextChoices):
        ASISTIO = "ASISTIO", _("✅ Asistió Normal")
        TARDANZA = "TARDANZA", _("⚠️ Tardanza")
        FALTA = "FALTA", _("❌ Falta Injustificada")
        PERMISO = "PERMISO", _("📝 Permiso Autorizado")
        DESCANSO_MEDICO = "DESCANSO_MEDICO", _("🏥 Descanso Médico")
        DESCANSO_SUTRAN = "DESCANSO_SUTRAN", _("🛑 Descanso Obligatorio SUTRAN (8h)")
        DIA_LIBRE = "DIA_LIBRE", _("🏖️ Día Libre / Feriado")

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumenes_asistencia",
        verbose_name="Colaborador",
    )
    fecha = models.DateField(db_index=True, verbose_name="Fecha de Asistencia")
    
    # Horas registradas en el día
    primera_entrada = models.TimeField(null=True, blank=True, verbose_name="Primera Entrada")
    ultima_salida = models.TimeField(null=True, blank=True, verbose_name="Última Salida")
    
    # Cálculos contables y de planillas (D.L. 728 / Normativa Laboral Peruana)
    minutos_tardanza = models.PositiveIntegerField(
        default=0,
        verbose_name="Minutos de Tardanza",
    )
    horas_trabajadas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Horas Efectivas Trabajadas",
    )
    horas_extras_25 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="HH.EE. al 25% (2 primeras horas)",
    )
    horas_extras_35 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="HH.EE. al 35% (a partir de 3ra hora)",
    )
    horas_nocturnas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Horas Nocturnas (22:00 a 06:00)",
    )

    # Conteo específico para Conductores (Evita error #¿NOMBRE? en Excel original)
    vueltas_codigo = models.CharField(
        max_length=20,
        default="0",
        verbose_name="Código de Vuelta Chofer",
        help_text="'0'=Sin ruta, 'X'=Vuelta Simple, 'XX'=Vuelta Doble, 'D'=Descanso",
    )
    total_vueltas_num = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Total Numérico de Vueltas",
    )

    estado = models.CharField(
        max_length=25,
        choices=EstadoAsistencia.choices,
        default=EstadoAsistencia.ASISTIO,
        verbose_name="Estado de Asistencia",
    )
    observaciones = models.TextField(
        blank=True,
        default="",
        verbose_name="Observaciones / Justificaciones",
    )
    verificado_contabilidad = models.BooleanField(
        default=False,
        verbose_name="Verificado por Contadora (CPC. Yaneli Terrones)",
    )

    class Meta:
        verbose_name = "Resumen de Asistencia Diaria"
        verbose_name_plural = "Resúmenes de Asistencia Diaria (Planilla)"
        ordering = ["-fecha", "usuario__last_name"]
        unique_together = ("usuario", "fecha")
        indexes = [
            models.Index(fields=["fecha", "estado"]),
            models.Index(fields=["usuario", "fecha"]),
        ]

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} | {self.usuario.nombre_completo} | {self.get_estado_display()} | Vueltas: {self.vueltas_codigo}"


class CargaArchivoAsistencia(models.Model):
    """
    Registro de auditoría de archivos Excel subidos por la Contadora General
    (ej. `ASISTENCIA AGOSTO 2026.xlsx`) procesados mediante Pandas.
    """

    class EstadoCarga(models.TextChoices):
        PENDIENTE = "PENDIENTE", _("⏳ Pendiente de Procesamiento")
        PROCESANDO = "PROCESANDO", _("⚙️ Procesando con Pandas...")
        COMPLETADO = "COMPLETADO", _("✅ Procesado Exitosamente")
        ERROR = "ERROR", _("❌ Error en Formato / Lectura")

    archivo = models.FileField(
        upload_to="asistencia/archivos_excel/",
        verbose_name="Archivo Excel ZKTeco (.xlsx / .xls / .dat)",
    )
    nombre_archivo_original = models.CharField(
        max_length=255,
        verbose_name="Nombre Original del Archivo",
    )
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuario que Subió el Archivo",
    )
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora de Subida",
    )
    mes_periodo = models.CharField(
        max_length=7,
        verbose_name="Periodo Mensual (YYYY-MM)",
        help_text="Ejemplo: 2026-08 para Agosto 2026",
    )
    total_filas_procesadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Filas de Marcaciones Leídas",
    )
    total_empleados_identificados = models.PositiveIntegerField(
        default=0,
        verbose_name="Trabajadores Encontrados",
    )
    total_horas_extras_25 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name="Total HH.EE. 25% Calculadas",
    )
    total_horas_extras_35 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name="Total HH.EE. 35% Calculadas",
    )
    total_vueltas_conductores = models.PositiveIntegerField(
        default=0,
        verbose_name="Total de Vueltas de Choferes Calculadas",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoCarga.choices,
        default=EstadoCarga.COMPLETADO,
        verbose_name="Estado del Procesamiento",
    )
    detalle_log = models.TextField(
        blank=True,
        default="",
        verbose_name="Detalle de Resultados y Alertas",
    )

    class Meta:
        verbose_name = "Auditoría de Carga Excel ZKTeco"
        verbose_name_plural = "Historial de Cargas Excel ZKTeco"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return f"{self.nombre_archivo_original} ({self.mes_periodo}) — {self.get_estado_display()}"
