import os
import unittest

os.environ.setdefault("LECTURIA_API_KEY", "test-key")

import app as app_module


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


if __name__ == "__main__":
    unittest.main()
