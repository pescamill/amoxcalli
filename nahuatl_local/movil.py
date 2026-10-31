"""Amoxcalli sin servidor: la misma aplicación dentro del navegador del teléfono (Pyodide).

La página no habla con un servidor: cada petición a /api/… llega aquí y la atiende el mismo manejador HTTP que usa
``platform serve``, con las mismas rutas, permisos y errores. Solo cambia el transporte: bytes en memoria en vez de
un socket. También funciona con CPython (pruebas y construcción de la versión web).
"""
import io
from http.cookies import SimpleCookie
from .community import DEFAULT_DB
from .corpus import CorpusStore
from .platform import make_app

HOST = 'amoxcalli.movil'


class _Socket:
    """Lo mínimo de un socket para BaseHTTPRequestHandler: entrega la petición y junta la respuesta."""

    def __init__(self, raw):
        self.raw, self.sent = raw, bytearray()

    def makefile(self, *args, **kwargs):
        return io.BytesIO(self.raw)

    def sendall(self, data):
        self.sent += data

    def settimeout(self, value):
        pass


class _Server:
    """Lo que el manejador consulta del servidor: instalación personal, sin proxy y un solo host."""
    demo = False
    public_origin = None
    allowed_hosts = {HOST}


class App:
    """Una instalación de Amoxcalli en memoria. La sesión de Voces se guarda junto a la base, como una cookie."""

    def __init__(self, db=DEFAULT_DB):
        self.handler = make_app(CorpusStore(db))
        self.session_file = db.with_name('sesion-movil.txt')
        self.cookie = self.session_file.read_text().strip() if self.session_file.exists() else ''
        self.server = _Server()

    def request(self, method, path, body=b'', content_type='application/json'):
        """Atiende una petición (ruta con su consulta, ya codificada) y devuelve (estado, cabeceras, cuerpo)."""
        # En Pyodide el cuerpo llega como Uint8Array de JavaScript.
        body = body.to_bytes() if hasattr(body, 'to_bytes') else body.encode() if isinstance(body, str) else bytes(body or b'')
        head = [f'{method} {path} HTTP/1.1', f'Host: {HOST}', f'Origin: http://{HOST}']
        if self.cookie:
            head.append(f'Cookie: {self.cookie}')
        if body:
            head += [f'Content-Type: {content_type}', f'Content-Length: {len(body)}']
        sock = _Socket(('\r\n'.join(head) + '\r\n\r\n').encode('latin-1') + body)
        self.handler(sock, ('movil', 0), self.server)
        status, headers, payload = _parse(bytes(sock.sent))
        for name, value in headers:
            if name.lower() == 'set-cookie':
                self._keep(value)
        return status, headers, payload

    def _keep(self, header):
        cookie = SimpleCookie()
        cookie.load(header)
        item = cookie.get('voces_session')
        if item is None:
            return
        self.cookie = '' if item['max-age'] == '0' or not item.value else f'voces_session={item.value}'
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_file.write_text(self.cookie)

    def warm_stages(self):
        """Las etapas de la preparación, en orden: quien llama atiende peticiones entre una y otra."""
        return list(self.handler.warm_stages)


def _parse(raw):
    head, _, body = raw.partition(b'\r\n\r\n')
    lines = head.decode('latin-1').split('\r\n')
    status = int(lines[0].split(' ', 2)[1])
    headers = [tuple(part.strip() for part in line.split(':', 1)) for line in lines[1:] if ':' in line]
    return status, headers, body
