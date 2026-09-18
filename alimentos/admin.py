from django.contrib import admin

from .models import PlanAlimentacion, RegistroAlimentacion, TipoAlimento


admin.site.register(TipoAlimento)
admin.site.register(PlanAlimentacion)
admin.site.register(RegistroAlimentacion)
