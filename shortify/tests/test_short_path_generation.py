from random import seed
from unittest import TestCase

from shortify.utils import gen_short_path


class ShortPathGenerationTestCase(TestCase):
    def setUp(self):
        seed("test seed")

    def test_short_path_generation(self):
        path = gen_short_path()
        self.assertEqual("eKOs6o", path)

        path = gen_short_path()
        self.assertEqual("70PiG3", path)
