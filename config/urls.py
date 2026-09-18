from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('publico.urls')),
    path('panel/', include('panel.urls')),
    path('panel/inventario/', include('inventario.urls')),
    path('panel/registro/', include('registro.urls')),
    path('panel/vacunas/', include('vacunas.urls')),
    path('panel/alimentos/', include('alimentos.urls')),
    path('panel/inseminacion/', include('inseminacion.urls')),
    path('panel/reportes/', include('reportes.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
