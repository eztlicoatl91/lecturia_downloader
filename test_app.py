import os
import unittest

os.environ.setdefault("LECTURIA_API_KEY", "test-key")

import app as app_module
from lecturia_to_epub import build_epub_from_lecturia


class GeneradorEpubApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_requiere_api_key_si_esta_configurada(self):
        response = self.client.post("/generar", json={"url": "https://example.com/cuento"})
        self.assertEqual(response.status_code, 401)

    def test_rechaza_peticion_sin_url(self):
        response = self.client.post(
            "/generar",
            json={},
            headers={"x-api-key": "test-key"},
        )
        self.assertEqual(response.status_code, 400)

    def test_genera_epub_real_y_devuelve_ruta(self):
        output_file = r"D:\Users\Isra\Documents\generador-epub\test_epub_local.epub"
        generated = build_epub_from_lecturia(
            "https://lecturia.org/cuentos-y-relatos/robert-bloch-la-progenie-de-bubastis/29062/",
            output_file=output_file,
        )
        self.assertTrue(os.path.exists(generated))
        self.assertTrue(os.path.getsize(generated) > 0)


if __name__ == "__main__":
    unittest.main()
