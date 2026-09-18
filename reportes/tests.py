from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ReportesViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='test')
        self.client.login(username='tester', password='test')

    def test_index_muestra_tarjetas(self):
        response = self.client.get(reverse('reportes:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inventario de insumos')
        self.assertContains(response, 'Cerdos en granja')
        self.assertContains(response, 'Reproductivo')

    def test_tipo_invalido_404(self):
        response = self.client.get('/panel/reportes/no-existe/')
        self.assertEqual(response.status_code, 404)

    def test_ver_produccion_sin_datos(self):
        response = self.client.get(reverse('reportes:ver', args=['produccion']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cerdos en granja')
