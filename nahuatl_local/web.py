"""Servidor HTTP único: enrutado, errores, cabeceras, hosts y archivos estáticos. Solo biblioteca estándar."""
import contextlib
import json
import sqlite3
import sys
import traceback
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from .community import MAX_AUDIO, Problem

# Solo el catálogo glífico aprobado puede servir imágenes externas.
CONTENT_SECURITY_POLICY = ("default-src 'self'; script-src 'self'; style-src 'self'; "
                           "img-src 'self' data: https://aztecglyphs.wired-humanities.org https://tlachia.iib.unam.mx; "
                           "media-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
MIME = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
        '.svg': 'image/svg+xml', '.png': 'image/png', '.webmanifest': 'application/manifest+json',
        '.md': 'text/plain; charset=utf-8'}


class Router:
    """Tabla explícita (método, ruta) → función. Los prefijos reciben el último segmento en `request.tail`."""

    def __init__(self):
        self.exact = {}
        self.prefixes = {}

    def add(self, method, path, function, prefix=False):
        methods = (self.prefixes if prefix else self.exact).setdefault(path, {})
        if method in methods:
            raise ValueError(f'Ruta duplicada: {method} {path}')
        methods[method] = function

    def resolve(self, method, path):
        candidates = [(self.exact.get(path, {}), None)]
        candidates += [(methods, path[len(prefix):]) for prefix, methods in self.prefixes.items()
                       if path.startswith(prefix) and path[len(prefix):] and '/' not in path[len(prefix):]]
        for methods, tail in candidates:
            if method in methods:
                return methods[method], tail
        if any(methods for methods, _ in candidates):
            raise Problem('Método no permitido.', 405)
        raise Problem('Ruta no encontrada.', 404)


class Static:
    """Alias explícitos más los archivos de primer nivel de un directorio, por extensión conocida."""

    def __init__(self, directory, aliases):
        self.directory = directory
        self.aliases = aliases

    def find(self, path):
        if path in self.aliases:
            return self.aliases[path]
        name = path[1:]
        if not name or '/' in name or '\\' in name or name.startswith('.'):
            return None
        candidate = self.directory / name
        return candidate if candidate.suffix in MIME and candidate.is_file() else None


def handler(store, router, static):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'Amoxcalli/1'

        def log_message(self, fmt, *args):
            # No registra textos, cookies ni direcciones de los participantes.
            pass

        def reply(self, value, status=200, mime='application/json; charset=utf-8', cookie=None):
            body = json.dumps(value, ensure_ascii=False).encode() if mime.startswith('application/json') else value
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', CONTENT_SECURITY_POLICY)
            self.send_header('Permissions-Policy', 'microphone=(self), camera=(), geolocation=()')
            if cookie:
                self.send_header('Set-Cookie', cookie)
            self.end_headers()
            self.wfile.write(body)

        def arg(self, name, default=''):
            return self.query.get(name, [default])[0]

        def get_person(self, required=False):
            cookies = SimpleCookie()
            with contextlib.suppress(Exception):
                cookies.load(self.headers.get('Cookie', ''))
            item = cookies.get('voces_session')
            person = store.person(item.value if item else '')
            if required and person is None:
                raise Problem('Elige tu variante y crea tu perfil para participar.', 401)
            return person

        def body(self, raw=False):
            try:
                n = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise Problem('Tamaño de envío inválido.') from None
            if not 0 < n <= (MAX_AUDIO if raw else 32_768):
                raise Problem('El envío está vacío o es demasiado grande.', 413)
            data = self.rfile.read(n)
            if raw:
                return data
            try:
                value = json.loads(data)
            except (ValueError, UnicodeDecodeError):
                raise Problem('No se pudo leer el envío.') from None
            if not isinstance(value, dict):
                raise Problem('El envío debe ser un objeto.')
            return value

        def dispatch(self):
            parsed = urlparse(self.path)
            self.query, self.query_string = parse_qs(parsed.query), parsed.query
            if self.command != 'GET':
                # Rechaza escritura entre sitios y solicitudes sin Origin permitido.
                expected = self.server.public_origin or f'http://{self.headers.get("Host", "")}'
                if self.headers.get('Origin', '') != expected:
                    raise Problem('Origen de envío no permitido.', 403)
            elif (file := static.find(parsed.path)):
                return self.reply(file.read_bytes(), mime=MIME[file.suffix])
            function, self.tail = router.resolve(self.command, parsed.path)
            return function(self)

        def handle_request(self):
            self.connection.settimeout(20)
            # Impide DNS rebinding en el servidor local; proxy HTTPS mediante --public-origin.
            if self.headers.get('Host', '') not in self.server.allowed_hosts:
                return self.reply({'error': 'Host no permitido.'}, 403)
            try:
                self.dispatch()
            except Problem as error:
                self.reply({'error': str(error)}, error.status)
            except (sqlite3.Error, ValueError, TypeError, KeyError):
                self.reply({'error': 'No se pudo guardar. Revisa los campos e inténtalo de nuevo.'}, 400)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            except Exception:
                # Sin consulta ni cuerpo en el registro: pueden contener textos de participantes.
                sys.stderr.write(f'Error interno en {self.command} {urlparse(self.path).path}\n{traceback.format_exc()}')
                self.reply({'error': 'Error interno del servidor. El detalle quedó en el registro local.'}, 500)

        do_GET = do_POST = do_DELETE = handle_request
    return Handler


class Server(ThreadingHTTPServer):
    # Una página pide ~20 recursos a la vez; macOS descarta conexiones por encima de la cola (5 por omisión).
    request_queue_size = 64

    def __init__(self, address, handler_class, public_origin=None):
        super().__init__(address, handler_class)
        host, port = address[0], self.server_address[1]
        self.public_origin = None
        self.allowed_hosts = {f'localhost:{port}', f'127.0.0.1:{port}', f'{host}:{port}'}
        if public_origin:
            p = urlparse(public_origin)
            if p.scheme != 'https' or not p.hostname or p.path not in ('', '/') or p.query or p.fragment or p.username:
                self.server_close()
                raise Problem('--public-origin requiere un origen HTTPS sin ruta.')
            self.public_origin = public_origin.rstrip('/')
            self.allowed_hosts.add(p.netloc)
