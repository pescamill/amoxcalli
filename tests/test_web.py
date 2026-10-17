"""Servidor único: tabla de rutas, errores JSON, cabeceras, hosts, Origin y estáticos."""
import contextlib
import http.client
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path

from nahuatl_local.community import Problem
from nahuatl_local.corpus import CorpusStore
from nahuatl_local.platform import STATIC, WEB, make_server
from nahuatl_local.web import MIME, Router, Server, Static, handler


class RouterTests(unittest.TestCase):
    def test_exact_prefix_and_method(self):
        router = Router()
        router.add('GET', '/a', 'get-a')
        router.add('DELETE', '/a/', 'delete-item', prefix=True)
        self.assertEqual(router.resolve('GET', '/a'), ('get-a', None))
        self.assertEqual(router.resolve('DELETE', '/a/x1'), ('delete-item', 'x1'))
        for method, path, status in [('POST', '/a', 405), ('GET', '/a/x1', 405), ('GET', '/b', 404),
                                     ('DELETE', '/a/', 404), ('DELETE', '/a/x/y', 404)]:
            with self.subTest(method=method, path=path), self.assertRaises(Problem) as error:
                router.resolve(method, path)
            self.assertEqual(error.exception.status, status)
        with self.assertRaises(ValueError):
            router.add('GET', '/a', 'again')

    def test_static_serves_only_top_level_known_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'a.js').write_text('1')
            (root / 'notes.txt').write_text('x')
            (root / 'sub').mkdir()
            (root / 'sub/b.js').write_text('2')
            static = Static(root, {'/': root / 'a.js'})
            self.assertEqual(static.find('/'), root / 'a.js')
            self.assertEqual(static.find('/a.js'), root / 'a.js')
            for path in ('/notes.txt', '/sub/b.js', '/../a.js', '/.hidden.js', '/missing.js', '/sub'):
                self.assertIsNone(static.find(path), path)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.httpd = make_server(CorpusStore(Path(cls.temp.name) / 'web.sqlite3'), port=0)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, method, path, body=None, port=None, **headers):
        conn = http.client.HTTPConnection('127.0.0.1', port or self.port, timeout=30)
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            return response, response.read()
        finally:
            conn.close()

    def assert_secure(self, response):
        self.assertEqual(response.getheader('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.getheader('X-Frame-Options'), 'DENY')
        self.assertEqual(response.getheader('Cache-Control'), 'no-store')
        self.assertIn("frame-ancestors 'none'", response.getheader('Content-Security-Policy'))

    def test_one_process_serves_app_voces_and_api(self):
        self.assertGreaterEqual(self.httpd.request_queue_size, 64)
        for path, mime in [('/', 'text/html'), ('/aportar', 'text/html'), ('/app.js', 'text/javascript'),
                           ('/corpus.js', 'text/javascript'), ('/favicon.svg', 'image/svg+xml'),
                           ('/project/purpose.md', 'text/plain'), ('/api/bootstrap', 'application/json'),
                           ('/api/system', 'application/json')]:
            with self.subTest(path=path):
                response, _ = self.request('GET', path)
                self.assertEqual(response.status, 200)
                self.assertTrue(response.getheader('Content-Type').startswith(mime))
                self.assert_secure(response)

    def test_every_interface_file_is_served_with_its_type(self):
        for file in sorted(WEB.iterdir()):
            if file.suffix not in MIME or file.name in ('app.js', 'style.css'):
                continue  # app.js y style.css de la aplicación se sirven como /corpus.js y /corpus.css.
            with self.subTest(file=file.name):
                response, body = self.request('GET', '/' + file.name)
                self.assertEqual(response.status, 200)
                self.assertEqual(response.getheader('Content-Type'), MIME[file.suffix])
                self.assertEqual(body, file.read_bytes())
        self.assertEqual(STATIC.find('/corpus.js'), WEB / 'app.js')

    def test_errors_are_json_with_security_headers(self):
        origin = f'http://127.0.0.1:{self.port}'
        cases = [('GET', '/api/nothing', {}, 404), ('GET', '/project/../../data/community/voces.sqlite3', {}, 404),
                 ('POST', '/api/proposals/x', {'Origin': origin}, 405), ('GET', '/api/compose', {}, 404),
                 ('POST', '/api/proposals', {'Origin': 'https://attacker.example'}, 403),
                 ('POST', '/api/proposals', {}, 403), ('GET', '/api/bootstrap', {'Host': 'evil.example'}, 403),
                 ('GET', '/api/mine', {}, 401), ('GET', '/api/explain?q=agua&model=otro', {}, 400)]
        for method, path, headers, status in cases:
            with self.subTest(method=method, path=path):
                response, body = self.request(method, path, **headers)
                self.assertEqual(response.status, status)
                self.assertTrue(response.getheader('Content-Type').startswith('application/json'))
                self.assertIn('error', json.loads(body))
                self.assert_secure(response)

    def test_unexpected_failure_answers_500_json_and_logs_without_query(self):
        router = Router()

        def broken(request):
            raise RuntimeError('fallo de prueba')
        router.add('GET', '/broken', broken)
        httpd = Server(('127.0.0.1', 0), handler(None, router, Static(WEB, {})))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
        log = io.StringIO()
        try:
            with contextlib.redirect_stderr(log):
                response, body = self.request('GET', '/broken?texto=privado', port=httpd.server_address[1])
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join()
        self.assertEqual(response.status, 500)
        self.assertIn('Error interno', json.loads(body)['error'])
        self.assertIn('RuntimeError: fallo de prueba', log.getvalue())
        self.assertNotIn('privado', log.getvalue())

    def test_public_origin_must_be_https_without_path(self):
        for origin in ('http://example.org', 'https://example.org/app', 'https://user@example.org'):
            with self.subTest(origin=origin), self.assertRaises(Problem):
                Server(('127.0.0.1', 0), handler(None, Router(), Static(WEB, {})), origin)
        httpd = Server(('127.0.0.1', 0), handler(None, Router(), Static(WEB, {})), 'https://example.org/')
        try:
            self.assertEqual(httpd.public_origin, 'https://example.org')
            self.assertIn('example.org', httpd.allowed_hosts)
        finally:
            httpd.server_close()


if __name__ == '__main__':
    unittest.main()
