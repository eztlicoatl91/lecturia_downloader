import unittest
import json
from app_local import app

class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lecturia a EPUB", response.data)
        self.assertIn(b"Kindle Paperwhite Edition", response.data)

    def test_descargar_missing_url(self):
        response = self.client.post("/descargar", json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_descargar_invalid_url(self):
        response = self.client.post("/descargar", json={"url": "not-a-url"})
        self.assertEqual(response.status_code, 400)

    def test_descargar_real_story(self):
        test_url = "https://lecturia.org/cuentos-y-relatos/robert-bloch-la-progenie-de-bubastis/29062/"
        response = self.client.post("/descargar", json={"url": test_url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/epub+zip")
        self.assertTrue(len(response.data) > 1000)

if __name__ == "__main__":
    unittest.main()
