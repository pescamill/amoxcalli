"""Precalienta los índices perezosos del servidor de prueba antes de las suites DOM.

En un clon limpio (CI) el primer uso de cada índice puede tardar más que las esperas
de jsdom. Se llaman en el mismo proceso del servidor; los errores HTTP se ignoran
porque solo importa construir los índices.
"""
import urllib.error
import urllib.request

PATHS = ('/api/corpus', '/api/learning', '/api/units', '/api/word?w=calli', '/api/ask?q=calli',
         '/api/terms?q=calli', '/api/ask/cards?q=calli', '/api/research?query=chachalaca&variant=nci')


def prewarm(origin):
    for path in PATHS:
        try:
            urllib.request.urlopen(origin + path, timeout=600).read()
        except urllib.error.HTTPError:
            pass
