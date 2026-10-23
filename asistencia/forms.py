import re
from django import forms
from asistencia.models import Trabajador, MarcacionBiometrica, IdentidadBiometrica
from django.db.models import Q


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ["nombre_completo", "dni", "area"]

    def clean_dni(self):
        dni = self.cleaned_data["dni"].strip()
        if not re.fullmatch(r"[0-9]{8}", dni):
            raise forms.ValidationError("Ingrese un DNI de 8 dígitos.")
        return dni

    def clean_nombre_completo(self):
        nombre = " ".join(self.cleaned_data["nombre_completo"].split())
        if len(nombre.split()) < 2:
            raise forms.ValidationError("Ingrese nombres y apellidos completos.")
        return nombre


class MarcacionManualForm(forms.Form):
    fecha_manual = forms.DateField(label="Fecha", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    hora_manual = forms.TimeField(label="Hora confirmada", widget=forms.TimeInput(attrs={"type": "time", "step": "1"}, format="%H:%M:%S"))
    tipo_evento_manual = forms.ChoiceField(label="Tipo de marcación", choices=[(codigo, nombre) for codigo, nombre in MarcacionBiometrica.TipoEvento.choices if codigo != "SIN_CLASIFICAR"])
    identidad_manual = forms.ModelChoiceField(label="Código importado / equipo", queryset=IdentidadBiometrica.objects.none(), required=False, widget=forms.HiddenInput())
    motivo_manual = forms.CharField(label="Motivo y referencia de la hora confirmada", max_length=1000, widget=forms.Textarea(attrs={"rows": 2}))
    evidencia_manual_url = forms.URLField(label="Enlace de evidencia (opcional)", required=False, max_length=500, widget=forms.HiddenInput())

    def __init__(self, *args, resumen, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["fecha_manual"] = resumen.fecha
        consulta = Q(pk__in=[])
        if resumen.trabajador_id:
            consulta |= Q(trabajador_id=resumen.trabajador_id)
        if resumen.usuario_id:
            consulta |= Q(usuario_id=resumen.usuario_id)
        identidades = IdentidadBiometrica.objects.filter(consulta)
        self.fields["identidad_manual"].queryset = identidades
        self._identidad_automatica = None
        self.fields["identidad_manual"].required = False
        if identidades.count() == 1:
            self._identidad_automatica = identidades.first()
        elif identidades.exists():
            from asistencia.services.revision import marcas_persona, ventana_jornada
            inicio, fin = ventana_jornada(resumen)
            ids = MarcacionBiometrica.objects.filter(
                marcas_persona(resumen), fecha_hora__gte=inicio, fecha_hora__lte=fin,
                es_valida=True, identidad_biometrica__in=identidades,
            ).values_list("identidad_biometrica_id", flat=True).distinct()
            usadas = list(identidades.filter(pk__in=ids)[:2])
            if len(usadas) == 1:
                self._identidad_automatica = usadas[0]
        if self._identidad_automatica:
            self.initial["identidad_manual"] = self._identidad_automatica.pk

    def clean_identidad_manual(self):
        identidad = self.cleaned_data.get("identidad_manual") or self._identidad_automatica
        if identidad is None and self.fields["identidad_manual"].queryset.exists():
            raise forms.ValidationError("No se pudo determinar el código de esta jornada. Revise la asociación del trabajador en el importador.")
        return identidad
