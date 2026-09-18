from django.contrib import admin

from .models import AplicacionVacuna, Vacuna


admin.site.register(Vacuna)
admin.site.register(AplicacionVacuna)
