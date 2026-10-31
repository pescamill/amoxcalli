"""Versión del teléfono: el adaptador en memoria responde como el servidor y conserva lo guardado."""
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local.movil import App

ITEM = dict(target='axolotl-00602', category='traduccion', basis='fuente', note='Falta «una mujer»')


class MovilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / 'voces.sqlite3'
        cls.app = App(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def get(self, path):
        status, headers, body = self.app.request('GET', path)
        return status, dict(headers), json.loads(body) if body else None

    def test_same_routes_and_errors_as_the_server(self):
        status, headers, data = self.get('/api/terms?q=cualli')
        self.assertEqual(status, 200)
        self.assertTrue(headers['Content-Type'].startswith('application/json'))
        self.assertTrue(data)
        self.assertEqual(self.get('/api/no-existe')[0], 404)
        self.assertEqual(self.get('/api/proposals')[0], 401)  # sin perfil, igual que en la computadora

    def test_writes_are_accepted_and_kept_with_the_database(self):
        status, _, body = self.app.request('POST', '/api/aclaraciones', json.dumps(ITEM))
        self.assertEqual(status, 201)
        saved = json.loads(body)['id']
        # Otra instancia sobre la misma carpeta (la página se recargó) ve la aclaración.
        again = App(self.db)
        _, _, body = again.request('GET', '/api/aclaraciones')
        self.assertIn(saved, [x['id'] for x in json.loads(body)['items']])
        self.assertEqual(again.request('DELETE', f'/api/aclaraciones/{saved}')[0], 200)

    def test_bad_body_is_a_clean_error(self):
        status, _, body = self.app.request('POST', '/api/aclaraciones', '{no es json')
        self.assertEqual(status, 400)
        self.assertIn('error', json.loads(body))

    def test_warm_stages_run_one_by_one(self):
        stages = self.app.warm_stages()
        self.assertEqual(len(stages), 5)
        for stage in stages:
            stage()
        _, _, data = self.get('/api/system')
        self.assertTrue(data['preparation']['ready'])


if __name__ == '__main__':
    unittest.main()
