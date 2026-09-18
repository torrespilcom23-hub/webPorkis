from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registro.models import Cerdo, CategoriaCerdo, Corral

from .forms import LechonesComunForm, PartoForm
from .models import DiagnosticoPrenez, Inseminacion, Parto, Padrillo


class PartoFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='test')
        self.corral = Corral.objects.create(nombre='C1', capacidad=20)
        self.categoria = CategoriaCerdo.objects.create(nombre='Cerda', peso_min=80, peso_max=200)
        hoy = timezone.now().date()
        self.cerda = Cerdo.objects.create(
            arete='H-0001',
            raza=Cerdo.Raza.LANDRACE,
            sexo=Cerdo.Sexo.HEMBRA,
            fecha_nacimiento=hoy - timedelta(days=400),
            categoria=self.categoria,
            corral=self.corral,
            estado=Cerdo.Estado.ACTIVO,
        )
        self.inseminacion = Inseminacion.objects.create(
            cerda=self.cerda,
            fecha=timezone.now().date() - timedelta(days=120),
            tipo=Inseminacion.Tipo.ARTIFICIAL,
            responsable=self.user,
        )
        DiagnosticoPrenez.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date() - timedelta(days=90),
            resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        )
        self.parto = Parto.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date() - timedelta(days=30),
            lechones_vivos=10,
        )

    def test_no_permite_vivos_menor_que_registrados(self):
        Cerdo.objects.create(
            arete='L-0001',
            raza=Cerdo.Raza.LANDRACE,
            sexo=Cerdo.Sexo.MACHO,
            fecha_nacimiento=self.parto.fecha,
            categoria=self.categoria,
            corral=self.corral,
            madre=self.cerda,
            parto=self.parto,
            estado=Cerdo.Estado.ACTIVO,
        )
        form = PartoForm(
            data={
                'inseminacion': self.inseminacion.pk,
                'fecha': self.parto.fecha.isoformat(),
                'lechones_vivos': 0,
                'lechones_muertos': 0,
                'lechones_destetados': '',
                'observaciones': '',
            },
            instance=self.parto,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('lechones_vivos', form.errors)


class LechonesComunFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='test')
        self.corral = Corral.objects.create(nombre='C1', capacidad=20)
        self.categoria = CategoriaCerdo.objects.create(nombre='Cerda', peso_min=80, peso_max=200)
        self.cerda = Cerdo.objects.create(
            arete='H-0002',
            raza=Cerdo.Raza.LANDRACE,
            sexo=Cerdo.Sexo.HEMBRA,
            fecha_nacimiento=timezone.now().date() - timedelta(days=400),
            categoria=self.categoria,
            corral=self.corral,
            estado=Cerdo.Estado.ACTIVO,
        )
        self.inseminacion = Inseminacion.objects.create(
            cerda=self.cerda,
            fecha=timezone.now().date() - timedelta(days=120),
            tipo=Inseminacion.Tipo.NATURAL,
            responsable=self.user,
        )
        DiagnosticoPrenez.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date() - timedelta(days=90),
            resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        )
        self.parto = Parto.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date() - timedelta(days=10),
            lechones_vivos=5,
        )

    def test_raza_otro_requerida(self):
        form = LechonesComunForm(
            data={
                'raza': Cerdo.Raza.OTRO,
                'raza_otro': '',
                'categoria': '',
                'corral': '',
                'lote': '',
                'crear_lote_camada': True,
            },
            parto=self.parto,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('raza_otro', form.errors)


class InseminacionViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='test')
        self.client.login(username='tester', password='test')
        self.corral = Corral.objects.create(nombre='C1', capacidad=20)
        self.categoria = CategoriaCerdo.objects.create(nombre='Cerda', peso_min=80, peso_max=200)
        self.cerda = Cerdo.objects.create(
            arete='H-0003',
            raza=Cerdo.Raza.LANDRACE,
            sexo=Cerdo.Sexo.HEMBRA,
            fecha_nacimiento=timezone.now().date() - timedelta(days=400),
            categoria=self.categoria,
            corral=self.corral,
            estado=Cerdo.Estado.ACTIVO,
        )
        self.padrillo = Padrillo.objects.create(codigo='DU-001', raza='Duroc')
        self.inseminacion = Inseminacion.objects.create(
            cerda=self.cerda,
            fecha=timezone.now().date() - timedelta(days=30),
            tipo=Inseminacion.Tipo.ARTIFICIAL,
            padrillo=self.padrillo,
            responsable=self.user,
        )

    def test_pestana_pendientes_desde_partos(self):
        response = self.client.get(reverse('inseminacion:partos'))
        self.assertContains(
            response,
            reverse('inseminacion:index') + '?vista=pendientes',
        )

    def test_eliminar_inseminacion_con_parto_bloqueada(self):
        admin = User.objects.create_superuser('admin', password='admin', email='a@test.com')
        self.client.login(username='admin', password='admin')
        DiagnosticoPrenez.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date(),
            resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        )
        Parto.objects.create(
            inseminacion=self.inseminacion,
            fecha=timezone.now().date(),
            lechones_vivos=8,
        )
        url = reverse('inseminacion:eliminar', args=[self.inseminacion.pk])
        response = self.client.post(url, follow=True)
        self.assertTrue(Inseminacion.objects.filter(pk=self.inseminacion.pk).exists())
        self.assertContains(response, 'parto(s) registrado(s)')
