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
    identidad_manual = forms.ModelChoiceField(label="Código importado / equipo", queryset=IdentidadBiometrica.objects.none(), required=False)
    motivo_manual = forms.CharField(label="Motivo y referencia de la hora confirmada", max_length=1000, widget=forms.Textarea(attrs={"rows": 2}))
    evidencia_manual_url = forms.URLField(label="Enlace de evidencia (opcional)", required=False, max_length=500)

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
        self.fields["identidad_manual"].required = identidades.exists()
        if identidades.count() == 1:
            self.initial["identidad_manual"] = identidades.first().pk
