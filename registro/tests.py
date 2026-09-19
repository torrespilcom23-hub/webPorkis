from django.test import SimpleTestCase

from registro.aretes import prefijo_categoria


class PrefijoAreteTest(SimpleTestCase):
    def test_sin_categoria(self):
        self.assertEqual(prefijo_categoria(None), 'SC')

    def test_una_palabra(self):
        class Cat:
            nombre = 'Chanchilla'

        self.assertEqual(prefijo_categoria(Cat()), 'CH')

    def test_dos_palabras(self):
        class Cat:
            nombre = 'Gorrino destetado'

        self.assertEqual(prefijo_categoria(Cat()), 'GD')

    def test_tres_palabras_ignora_de(self):
        class Cat:
            nombre = 'Pie de cría'

        self.assertEqual(prefijo_categoria(Cat()), 'PC')

    def test_parentesis(self):
        class Cat:
            nombre = 'Engorde (cebo)'

        self.assertEqual(prefijo_categoria(Cat()), 'EC')
