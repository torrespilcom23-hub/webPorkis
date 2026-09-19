from django.test import SimpleTestCase

from panel.views import mensajes_lista


class PanelViewsImportTest(SimpleTestCase):
    def test_mensajes_lista_is_callable(self):
        self.assertTrue(callable(mensajes_lista))
