"""Explicación con citas sobre la evidencia de ``evidence.Evidence``.

Dos redactores con el mismo contrato y el mismo validador:

* ``extractive`` (por omisión): frases fijas construidas solo con los campos de la
  evidencia. Cero llamadas a modelos.
* ``claude`` (opcional): Claude redacta una explicación breve usando únicamente la
  evidencia numerada. Se activa al arrancar el servidor con ``--explain-model claude``
  y credenciales de Anthropic. Envía a la API la pregunta y los pasajes citados.

``validate`` acepta una explicación solo si cada frase cita IDs de la evidencia y las
formas nahuas entre «» aparecen en lo citado. Una explicación del modelo que no pasa
la validación se descarta y se muestra la extractiva, con el motivo.
"""
import re

from .evidence import loose_key

EXPLAIN_VERSION = 'explain-cited-v1'
CLAUDE_MODEL = 'claude-opus-5-5'
CITE = re.compile(r'\[((?:axolotl-\d{5}|sense-[\w-]+)(?:\s*[,;]\s*(?:axolotl-\d{5}|sense-[\w-]+))*)\]')
QUOTE = re.compile(r'«([^»]{1,80})»')
MAX_SENTENCES = 6


def _clip(text, limit=160):
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


def bundle(result):
    """Evidencia citable: ID → texto que la respalda (náhuatl, traducción o definición)."""
    items = {}
    for e in result.get('entries', []):
        items[e['sense_id']] = dict(kind='entry', id=e['sense_id'], text=f"{e['written']}: {e['label']}",
                                    written=e['written'], label=e['label'])
    for p in result.get('passages', []) + result.get('other_varieties', []):
        items[p['id']] = dict(kind='passage', id=p['id'], text=f"{p['nah']} || {p['es']}", nah=p['nah'], es=p['es'],
                              form=p.get('form'), variety=p.get('variety'))
    return items


def sentences_of(text):
    """Divide en frases sin cortar dentro de «…» ni de […]."""
    text, out, start, depth = (text or '').strip(), [], 0, 0
    for i, ch in enumerate(text):
        if ch in '«[':
            depth += 1
        elif ch in '»]':
            depth = max(0, depth - 1)
        elif ch in '.!?' and depth == 0 and (i + 1 == len(text) or (text[i + 1] == ' ' and re.match(r'\s+[A-ZÁÉÍÓÚÑ«¿¡]', text[i + 1:]))):
            out.append(text[start:i + 1].strip()); start = i + 1
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def _norm(text):
    return re.sub(r'\s+', ' ', (text or '').casefold())


def validate(text, items, query_word=''):
    """Cada frase con ≥1 cita; IDs dentro de la evidencia; formas «…» presentes en lo citado."""
    errors, out = [], []
    sentences = sentences_of(text)
    if not sentences:
        errors.append('sin_texto')
    if len(sentences) > MAX_SENTENCES:
        errors.append('demasiado_larga')
    for s in sentences:
        ids = [i.strip() for m in CITE.finditer(s) for i in re.split(r'[,;]', m.group(1))]
        if not ids:
            errors.append('frase_sin_cita: ' + _clip(s, 60))
            continue
        unknown = [i for i in ids if i not in items]
        if unknown:
            errors.append('cita_fuera_de_evidencia: ' + ', '.join(unknown))
            continue
        support = _norm(' '.join(items[i]['text'] for i in ids) + ' ' + query_word)
        for q in QUOTE.findall(s):
            if _norm(q) not in support:
                errors.append(f'cita_textual_no_respaldada: «{q}»')
        out.append(dict(text=re.sub(r'\s+([.,;:])', r'\1', CITE.sub('', s)).strip(), citations=ids))
    return dict(valid=not errors, errors=errors, sentences=out)


def extractive(result):
    """Explicación sin modelo: cada frase se arma con campos de la evidencia y su ID."""
    s = []
    word = result['word']
    if result.get('abstained'):
        return ''
    if result['language'] == 'nah':
        a = result.get('analysis')
        entry = result['entries'][0] if result['entries'] else None
        if result.get('interpreted_as'):
            same = [p for p in result['passages'] if (p.get('form') or '').casefold() == result['interpreted_as'].casefold()]
            if same:
                s.append(f"«{word}» se lee aquí como «{result['interpreted_as']}», otra grafía del mismo vocablo en el archivo [{same[0]['id']}].")
        if a and entry:
            parts = ' + '.join(f"{m['surface'] or m['key']} ({m['gloss'] or m['tag']})" for m in a['morphemes'])
            s.append(f"El análisis automático propone {parts}; la raíz corresponde a la entrada «{entry['written']}», «{entry['label']}» [{entry['sense_id']}].")
        elif entry:
            s.append(f"El diccionario registra «{entry['written']}» como «{entry['label']}» [{entry['sense_id']}].")
        # Primero los pasajes con la misma palabra (en cualquier grafía); después los de la misma raíz.
        same = {loose_key(word)} | ({loose_key(result['interpreted_as'])} if result.get('interpreted_as') else set())
        exact = [p for p in result['passages'] if loose_key(p.get('form') or '') in same]
        for p in (exact or result['passages'])[:2]:
            if p.get('form'):
                s.append(f"En {p['document'] or 'el archivo'} aparece «{p['form']}»; la traducción de origen dice: «{_clip(p['es'], 120)}» [{p['id']}].")
        if result['other_varieties']:
            o = result['other_varieties'][0]
            s.append(f"También se escribe «{o['form']}» en un pasaje de {o['variety']} [{o['id']}].")
    else:
        if result['entries']:
            e = result['entries'][0]
            s.append(f"En el diccionario, «{e['written']}» se define como «{e['label']}» [{e['sense_id']}].")
        for c in result.get('candidates', [])[:2]:
            cited = c['passages'][:3]
            ids = [p['id'] for p in cited]
            forms = ', '.join(f"«{f}»" for f in dict.fromkeys(p['form'] for p in cited if p.get('form')))
            if ids:
                s.append(f"El corpus paralelo traduce «{word}» en {c['support']} pasajes con formas como {forms}; es una asociación estadística, no una definición [{', '.join(ids)}].")
        if not s and result['passages']:
            p = result['passages'][0]
            s.append(f"Hay pasajes cuya traducción dice «{word}», sin un equivalente náhuatl con apoyo suficiente [{p['id']}].")
    return ' '.join(s[:MAX_SENTENCES])


SYSTEM = (
    'Eres un asistente para estudiantes de náhuatl clásico. Explicas una palabra usando EXCLUSIVAMENTE la evidencia '
    'numerada que se te da: entradas de diccionario y pasajes con su traducción de origen. Reglas: '
    '1) Escribe en español, de 2 a 5 frases, sin listas ni encabezados. '
    '2) Termina cada frase con los IDs que la sustentan entre corchetes, por ejemplo [axolotl-00123] o [sense-calli]. '
    '3) No uses conocimiento externo ni propongas traducciones nuevas; si citas una forma náhuatl o española, ponla entre «» '
    'y cópiala tal como aparece en la evidencia citada. '
    '4) Distingue el análisis automático y las asociaciones estadísticas de una definición. '
    '5) Si la evidencia no basta, responde solo: No hay evidencia suficiente.'
)


def prompt(result, items):
    lines = [f"Consulta: {result['query']}", f"Palabra: {result['word']} ({'náhuatl' if result['language'] == 'nah' else 'español'})"]
    if result.get('interpreted_as'):
        lines.append(f"Leída como otra grafía: {result['interpreted_as']}")
    a = result.get('analysis')
    if a:
        lines.append('Análisis automático: ' + ' + '.join(f"{m['surface'] or m['key']} [{m['tag']}] {m['gloss']}".strip() for m in a['morphemes'])
                     + f" (base: {a['basis']})")
    for c in result.get('candidates', []):
        lines.append(f"Asociación estadística: raíz {c['stem']} en {c['support']} pasajes; formas: "
                     + ', '.join(f['form'] for f in c['forms'][:5]))
    lines.append('Evidencia:')
    for i in items.values():
        if i['kind'] == 'entry':
            lines.append(f"[{i['id']}] Entrada de diccionario: {i['written']} — {i['label']}")
        else:
            lines.append(f"[{i['id']}] Pasaje ({i['variety']}): {i['nah']} — Traducción de origen: {i['es']}")
    return '\n'.join(lines)


class ClaudeWriter:
    """Redactor opcional con Claude. Requiere el paquete ``anthropic`` y credenciales."""
    name = 'claude'

    def __init__(self, client=None, model=CLAUDE_MODEL):
        self.model = model
        self._client = client

    def client(self):
        if self._client is None:
            try:
                import anthropic  # dependencia opcional: pip install anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                raise RuntimeError('Falta el paquete anthropic; se muestra la explicación sin modelo.') from None
            except anthropic.AnthropicError:
                raise RuntimeError('No hay credenciales de Anthropic; se muestra la explicación sin modelo.') from None
        return self._client

    @staticmethod
    def _api_errors():
        try:
            import anthropic
        except ImportError:
            return ()
        return (anthropic.APIStatusError, anthropic.APIConnectionError)

    def write(self, result, items):
        client = self.client()
        try:
            response = client.beta.messages.create(
                model=self.model, max_tokens=16000, system=SYSTEM,
                output_config={'effort': 'medium'},
                betas=['server-side-fallback-2026-07-01'], fallbacks='default',
                messages=[{'role': 'user', 'content': prompt(result, items)}])
        except self._api_errors() as error:
            status = getattr(error, 'status_code', None)
            reason = 'la API está ocupada' if status == 429 else f'la API respondió {status}' if status else 'no se pudo conectar con la API'
            raise RuntimeError(f'No se pudo redactar con Claude ({reason}); se muestra la explicación sin modelo.') from None
        if response.stop_reason == 'refusal':
            raise RuntimeError('El modelo declinó la solicitud; se muestra la explicación sin modelo.')
        text = ''.join(b.text for b in response.content if b.type == 'text').strip()
        return text, dict(model=response.model, input_tokens=response.usage.input_tokens,
                          output_tokens=response.usage.output_tokens)


def explain(result, writer=None):
    """Devuelve la explicación validada; con ``writer`` intenta primero el modelo."""
    items = bundle(result)
    base = dict(version=EXPLAIN_VERSION, evidence_ids=sorted(items), model_calls=0)
    if result.get('abstained'):
        return dict(base, method='none', sentences=[], valid=True, note=result.get('reason', ''))
    fallback = None
    if writer is not None:
        try:
            text, usage = writer.write(result, items)
            base['model_calls'] = 1
            if text.strip().startswith('No hay evidencia suficiente'):
                fallback = 'El modelo indicó que la evidencia no basta.'
            else:
                checked = validate(text, items, result['word'])
                if checked['valid']:
                    return dict(base, method=writer.name, model=usage.get('model'), usage=usage,
                                sentences=checked['sentences'], valid=True,
                                note='Redactado por Claude solo con la evidencia mostrada; cada frase pasó la validación de citas. '
                                     'Pendiente de revisión lingüística.')
                fallback = 'La explicación del modelo no pasó la validación de citas: ' + '; '.join(checked['errors'][:3])
        except RuntimeError as error:
            fallback = str(error)
    checked = validate(extractive(result), items, result['word'])
    out = dict(base, method='extractive', sentences=checked['sentences'], valid=checked['valid'], errors=checked['errors'],
               note='Explicación armada con la evidencia mostrada, sin modelo. Pendiente de revisión lingüística.')
    if fallback:
        out['fallback_reason'] = fallback
    return out
