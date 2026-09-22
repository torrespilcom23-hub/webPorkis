from django.contrib.auth.models import Group, User
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from panel.decorators import puede_acceder_panel
from panel.mensajes_utils import normalizar_whatsapp


class WhatsappNumeroTest(SimpleTestCase):
    def test_movil_peru_nueve_digitos(self):
        self.assertEqual(normalizar_whatsapp('912 345 678'), '51912345678')

    def test_local_ocho_digitos_prefijo_pais(self):
        self.assertEqual(normalizar_whatsapp('13456665'), '5113456665')

    def test_con_codigo_pais(self):
        self.assertEqual(normalizar_whatsapp('+51 904 013 194'), '51904013194')


class PanelAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        Group.objects.get_or_create(name='admin')
        Group.objects.get_or_create(name='operador')

        self.admin = User.objects.create_user('admin_test', password='pass12345')
        self.admin.groups.add(Group.objects.get(name='admin'))

        self.operador = User.objects.create_user('oper_test', password='pass12345')
        self.operador.groups.add(Group.objects.get(name='operador'))

        self.sin_rol = User.objects.create_user('nada', password='pass12345')

    def test_puede_acceder_panel_grupos(self):
        self.assertTrue(puede_acceder_panel(self.admin))
        self.assertTrue(puede_acceder_panel(self.operador))
        self.assertFalse(puede_acceder_panel(self.sin_rol))

    def test_sin_rol_no_entra_al_panel_tras_login(self):
        self.client.login(username='nada', password='pass12345')
        response = self.client.get(reverse('panel:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/panel/login/', response.url)

    def test_operador_ve_dashboard_no_usuarios(self):
        self.client.login(username='oper_test', password='pass12345')
        self.assertEqual(self.client.get(reverse('panel:dashboard')).status_code, 200)
        response = self.client.get(reverse('panel:usuarios'))
        self.assertEqual(response.status_code, 302)

    def test_admin_gestiona_usuarios(self):
        self.client.login(username='admin_test', password='pass12345')
        response = self.client.get(reverse('panel:usuarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'oper_test')
