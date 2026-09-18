from django.contrib import admin

from .models import DiagnosticoPrenez, Inseminacion, Padrillo, Parto


admin.site.register(Padrillo)
admin.site.register(Inseminacion)
admin.site.register(DiagnosticoPrenez)
admin.site.register(Parto)
