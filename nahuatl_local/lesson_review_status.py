"""Diagnóstico público de vigencia de un paquete explícito, sin modificarlo."""
import argparse
import json
from pathlib import Path
import re

from .community import ROOT
from .editorial_pipeline import encoded
from .lesson_review_packet import digest, safe_path, verify

# Registro explícito del contrato público 009. No se descubren fuentes recorriendo
# carpetas ni se aceptan entradas nuevas de un manifiesto autodeclarado.
PUBLIC_SOURCES = frozenset({
    'THIRD_PARTY_NOTICES.md',
    'configs/documentary-evaluation-v1.json', 'configs/sources.json',
    'corpus/archive-source-v3.json', 'corpus/axolotl/axolotl.csv',
    'corpus/editorial-batch-007-v9.json', 'corpus/editorial-releases.json',
    'corpus/flor-lexicon-v8.json', 'corpus/gdn-lexicon-v6.json',
    'corpus/glyph-associations-v7.json', 'corpus/glyph-images-v4.json',
    'corpus/glyph-lexicon-v5.json', 'corpus/glyph-links-v2.json',
    'corpus/glyph-source-images-v5.json', 'corpus/learning-v1.json',
    'corpus/pictography/catalog.json', 'corpus/seed.json',
    'docs/CONSULTA_DOCUMENTAL.md', 'docs/EVALUACION_DOCUMENTAL.md',
    'docs/FUENTES.md', 'docs/ITERACIONES.md', 'docs/LABORATORIO.md',
    'docs/PILOTO_INSTITUCIONAL.md', 'docs/PROPOSITO.md',
    'docs/REVISION_LECTURA.md', 'docs/TRABAJO_AUTONOMO.md',
    'editorial/lesson-decisions.json',
    'nahuatl_local/community.py', 'nahuatl_local/community_web/catalog.json',
    'nahuatl_local/corpus.py', 'nahuatl_local/documentary_evaluation.py',
    'nahuatl_local/documentary_laboratory.py', 'nahuatl_local/documentary_retrieval.py',
    'nahuatl_local/documentary_retrieval_evaluation.py', 'nahuatl_local/editorial_pipeline.py',
    'nahuatl_local/iteration.py', 'nahuatl_local/laboratory.py',
    'nahuatl_local/learning.py', 'nahuatl_local/lesson_audit.py',
    'nahuatl_local/lesson_review_packet.py', 'nahuatl_local/model_status.py',
    'nahuatl_local/pictography.py', 'nahuatl_local/platform.py',
    'nahuatl_local/platform_web/app.js', 'nahuatl_local/platform_web/documentary.js',
    'nahuatl_local/platform_web/index.html', 'nahuatl_local/platform_web/laboratory.css',
    'nahuatl_local/platform_web/laboratory.js', 'nahuatl_local/platform_web/learning.js',
    'nahuatl_local/platform_web/project.js', 'nahuatl_local/platform_web/style.css',
    'nahuatl_local/platform_web/training-data.js', 'nahuatl_local/research.py',
    'reports/documentary-evaluation-validation-v1.json',
    'reports/documentary-laboratory-display-v1.json',
    'reports/documentary-laboratory-v1.json', 'reports/documentary-retrieval-v1.json',
    'scripts/test-platform-ui.py', 'tests/platform_ui.cjs',
    'tests/test_iteration.py', 'tests/test_laboratory.py',
})
FILES = frozenset({'package.json', 'package.md', 'human-decisions.blank.json'})
MEMBERS = FILES | {'manifest.json'}
# Evidence opened by the legacy reconstruction of existing historical decisions.
# It is checked for safe paths but never exported as decision content.
DECISION_EVIDENCE = frozenset({
    'reports/FLOR_CICLO_2026-09-30.md', 'reports/platform-ui-flor-2026-09-30.txt',
    'editorial/flor-beginner-trial.md', 'editorial/flor-source-extract.json',
    'reports/iterations/iteration-002/changes.md',
    'editorial/pictography-tlachia-telleriano-385-26v-v2-candidate-report.json',
    'editorial/pictography-tlachia-telleriano-385-26v-v2-candidate.json',
    'tests/test_pictography.py',
})
MANIFEST_FIELDS = {'schema_version', 'kind', 'sources', 'diagnostic_fingerprint', 'lesson_id', 'files'}
HEX = re.compile(r'[0-9a-f]{64}')
ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]*')
MESSAGES = {
    'package_unsafe': 'Ruta del paquete insegura; no se abre.',
    'package_missing': 'No existe el directorio del paquete.',
    'member_unsafe': 'Archivo del paquete inseguro; no se abre.',
    'member_missing': 'Falta un archivo obligatorio del paquete.',
    'member_not_file': 'El miembro obligatorio no es un archivo regular.',
    'member_extra': 'Hay un miembro adicional; no se lee su contenido.',
    'member_changed': 'Los bytes del archivo difieren del hash declarado.',
    'json_invalid': 'JSON ilegible, duplicado o inválido; no se copia su contenido.',
    'manifest_invalid': 'El manifiesto incumple campos, nombres o tipos del contrato 009.',
    'manifest_noncanonical': 'El manifiesto fue editado respecto a su codificación determinista.',
    'diagnostic_inputs_invalid': 'Las tres referencias de diagnóstico son inválidas.',
    'source_unknown': 'Entrada de fuente fuera del registro público admitido; no se abre.',
    'source_unsafe': 'Ruta de fuente insegura; no se abre ni se publica la ruta rechazada.',
    'source_hash_invalid': 'Hash de fuente inválido; se requiere SHA-256 hexadecimal.',
    'source_unlisted': 'Falta una fuente exigida por el contrato público.',
    'source_missing': 'La fuente ya no es un archivo disponible.',
    'source_changed': 'La fuente cambió respecto al SHA-256 previo.',
    'read_failed': 'No fue posible leer el archivo público.',
    'semantic_failed': 'La reconstrucción verify no confirmó el paquete completo.',
    'internal_references_invalid': 'Referencias internas que abriría verify fuera del contrato público o inseguras; no se reconstruye.',
}
LIMITS = [
    'Vigencia técnica no acredita revisión humana, cotejo lingüístico, derechos nuevos ni aprendizaje.',
    'Las revisiones y tareas humanas siguen pendientes; este comando no aplica decisiones ni cierra tareas.',
    'Si el paquete no es valid, regenerarlo en una carpeta nueva; conservar el paquete y las notas previas.',
    'Solo se informa metadata pública y hashes; no se copian claves, filas de reserva ni notas humanas.',
    'Las URLs no se consultan. No hay red, modelo ni lectura de datos privados.',
]


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Campo JSON duplicado.')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Constante JSON inválida.')))


def canonical_reference(value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('Referencia inválida.')
    path = safe_path(value)
    if str(path.relative_to(ROOT)) != value:
        raise ValueError('Referencia no canónica.')
    return path


def diagnostic_references(package):
    inputs = package.get('diagnostic_inputs') if isinstance(package, dict) else None
    if not isinstance(inputs, dict) or set(inputs) != {'inventory', 'queue', 'state'}:
        raise ValueError('Referencias inválidas.')
    # Admit only the three fixed diagnostic roles lexically here. Link safety is
    # checked for each source in the all-source preflight, so one unsafe role
    # cannot hide independent changes in the other two diagnostic sources.
    paths = {}
    for key, value in inputs.items():
        if (not isinstance(value, str) or not value or Path(value).is_absolute()
                or '..' in Path(value).parts or str(Path(value)) != value
                or Path(value).parts[0] != 'reports'):
            raise ValueError('Referencias inválidas.')
        paths[key] = ROOT / value
    if (paths['inventory'].name != 'inventory.json' or paths['queue'].name != 'queue.json'
            or paths['inventory'].parent != paths['queue'].parent
            or paths['state'].name != 'state.json'
            or any(p.relative_to(ROOT).parts[0] != 'reports' for p in paths.values())
            or len(set(paths.values())) != 3):
        raise ValueError('Referencias inválidas.')
    return set(inputs.values())


def reconstruction_preflight(package, source_raws):
    """Guard concrete indirect reads in legacy build before delegating to verify."""
    inputs = package['diagnostic_inputs']
    inventory = strict_json(source_raws[inputs['inventory']])
    if (not isinstance(inventory, dict) or not isinstance(inventory.get('sources'), dict)
            or set(inventory['sources']) - PUBLIC_SOURCES):
        raise ValueError('Fuentes internas desconocidas.')
    for reference, expected in inventory['sources'].items():
        canonical_reference(reference)
        if not isinstance(expected, str) or not HEX.fullmatch(expected):
            raise ValueError('Hash interno inválido.')
    state = strict_json(source_raws[inputs['state']])
    legacy = strict_json(source_raws['editorial/lesson-decisions.json'])
    if (not isinstance(state, dict) or not isinstance(state.get('tasks'), dict)
            or not isinstance(legacy, dict) or not isinstance(legacy.get('decisions'), dict)):
        raise ValueError('Decisiones internas inválidas.')
    decisions = []
    for row in state['tasks'].values():
        if not isinstance(row, dict) or not isinstance(row.get('decision', {}), dict):
            raise ValueError('Decisión interna inválida.')
        decisions.append(row.get('decision', {}))
    decisions.extend(legacy['decisions'].values())
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError('Decisión interna inválida.')
        evidence = decision.get('evidence', [])
        if not isinstance(evidence, list):
            raise ValueError('Evidencia interna inválida.')
        for reference in evidence:
            if not isinstance(reference, str) or reference not in PUBLIC_SOURCES | DECISION_EVIDENCE:
                raise ValueError('Evidencia interna desconocida.')
            canonical_reference(reference)
    releases = strict_json(source_raws['corpus/editorial-releases.json'])
    if not isinstance(releases, dict) or not isinstance(releases.get('releases'), list):
        raise ValueError('Publicaciones internas inválidas.')
    for release in releases['releases']:
        if not isinstance(release, dict) or not isinstance(release.get('bundle'), str):
            raise ValueError('Publicación interna inválida.')
        reference = 'corpus/' + release['bundle']
        if reference not in PUBLIC_SOURCES:
            raise ValueError('Publicación interna desconocida.')
        canonical_reference(reference)


def inspect_package(package_path):
    """Aggregate independent causes. Only verify's complete reconstruction can yield valid."""
    report = dict(schema_version=1, kind='reading_review_status', package=None,
                  state='invalid', ready=False, semantic_validation='not_run',
                  lesson_id=None, files=[], sources=[], issues=[], human_review='pending',
                  limits=LIMITS, network_requests=0, llm_calls=0)

    def issue(code, reference=None, **metadata):
        report['issues'].append(dict(code=code, message=MESSAGES[code],
                                     **({'reference': reference} if reference else {}), **metadata))

    try:
        output = safe_path(package_path, output=True)
    except (ValueError, TypeError):
        issue('package_unsafe')
        return report
    report['package'] = str(output.relative_to(ROOT))
    if not output.is_dir():
        issue('package_missing')
        return report

    # Preflight every member, including extras, before opening a package file.
    paths = {}
    try:
        names = {p.name for p in output.iterdir()} | MEMBERS
    except OSError:
        issue('read_failed')
        return report
    for name in sorted(names):
        if name not in MEMBERS:
            issue('member_extra')  # Untrusted names/notes are not copied to the report.
        try:
            path = safe_path(output / name)
        except ValueError:
            issue('member_unsafe', name if name in MEMBERS else None)
            continue
        if name not in MEMBERS:
            continue
        if not path.exists():
            issue('member_missing', name)
        elif not path.is_file():
            issue('member_not_file', name)
        else:
            paths[name] = path
    raws = {}
    for name, path in sorted(paths.items()):
        try:
            raws[name] = safe_path(path).read_bytes()
        except (OSError, ValueError):
            issue('read_failed', name)

    def load(name):
        if name not in raws:
            return None
        try:
            return strict_json(raws[name])
        except (ValueError, UnicodeError):
            issue('json_invalid', name)
            return None

    manifest = load('manifest.json')
    package = load('package.json')
    references = set()
    try:
        references = diagnostic_references(package)
    except (ValueError, TypeError):
        issue('diagnostic_inputs_invalid')
    valid_manifest = (isinstance(manifest, dict) and set(manifest) == MANIFEST_FIELDS
                      and type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1
                      and manifest.get('kind') == 'reading_review_manifest'
                      and isinstance(manifest.get('lesson_id'), str) and ID.fullmatch(manifest['lesson_id'])
                      and isinstance(manifest.get('diagnostic_fingerprint'), str)
                      and HEX.fullmatch(manifest['diagnostic_fingerprint'])
                      and isinstance(manifest.get('sources'), dict) and bool(manifest['sources'])
                      and isinstance(manifest.get('files'), dict) and set(manifest['files']) == FILES
                      and all(isinstance(v, str) and HEX.fullmatch(v) for v in manifest['files'].values()))
    if not valid_manifest:
        issue('manifest_invalid')
    else:
        report['lesson_id'] = manifest['lesson_id']
        if encoded(manifest) != raws['manifest.json']:
            issue('manifest_noncanonical')

    declared_files = manifest.get('files', {}) if isinstance(manifest, dict) else {}
    for name in sorted(FILES):
        expected = declared_files.get(name) if isinstance(declared_files, dict) else None
        expected = expected if isinstance(expected, str) and HEX.fullmatch(expected) else None
        current = digest(raws[name]) if name in raws else None
        report['files'].append(dict(reference=name, expected_sha256=expected, current_sha256=current))
        if expected is not None and current is not None and expected != current:
            issue('member_changed', name, expected_sha256=expected, current_sha256=current)

    sources = manifest.get('sources', {}) if isinstance(manifest, dict) else {}
    allowed = PUBLIC_SOURCES | references
    source_paths, source_raws = {}, {}
    needed_raws = references | {'corpus/editorial-releases.json', 'editorial/lesson-decisions.json'}
    if isinstance(sources, dict):
        # Validate all source paths/types before opening any source. Never trust a
        # new path simply because its author supplied a matching digest.
        for index, (reference, expected) in enumerate(sorted(sources.items())):
            try:
                path = canonical_reference(reference)
            except (ValueError, TypeError):
                issue('source_unsafe', entry_index=index)
                continue
            if reference not in allowed:
                issue('source_unknown', entry_index=index)
                continue
            if not isinstance(expected, str) or not HEX.fullmatch(expected):
                issue('source_hash_invalid', reference)
                continue
            source_paths[reference] = path
        for reference in sorted(allowed - set(sources)):
            issue('source_unlisted', reference)
        for reference, path in sorted(source_paths.items()):
            expected, current = sources[reference], None
            try:
                path = safe_path(path)
                if path.is_file():
                    raw = path.read_bytes()
                    current = digest(raw)
                    if reference in needed_raws:
                        source_raws[reference] = raw
                else:
                    issue('source_missing', reference, expected_sha256=expected, current_sha256=None)
            except (OSError, ValueError):
                issue('read_failed', reference)
            report['sources'].append(dict(reference=reference, expected_sha256=expected, current_sha256=current))
            if current is not None and current != expected:
                issue('source_changed', reference, expected_sha256=expected, current_sha256=current)
    if not report['issues']:
        try:
            reconstruction_preflight(package, source_raws)
        except (ValueError, UnicodeError, TypeError, KeyError):
            issue('internal_references_invalid')
    if not report['issues']:
        try:
            if verify(output) != 'valid':
                raise ValueError('Reconstrucción sin validación.')
        except (ValueError, OSError, TypeError, KeyError, IndexError, AttributeError) as error:
            report['semantic_validation'] = 'failed'
            issue('semantic_failed', error_type=type(error).__name__)
        else:
            report.update(state='valid', ready=True, semantic_validation='passed')
    elif all(item['code'] in {'source_changed', 'source_missing'} for item in report['issues']):
        report['state'] = 'stale'
    return report


def render(report):
    labels = {'valid': 'Vigente', 'stale': 'Obsoleto', 'invalid': 'Inválido'}
    lines = ['# Estado del paquete de revisión', '',
             'Paquete: ' + (report['package'] or 'ruta rechazada') + '.', '',
             f"Estado: **{labels[report['state']]}** (`{report['state']}`). Reconstrucción: `{report['semantic_validation']}`.", '',
             'Revisión humana: **pendiente**. Ninguna tarea se cierra.', '', '## Causas', '']
    if not report['issues']:
        lines.append('Sin discrepancias; verify reconstruyó y confirmó el paquete completo.')
    for item in report['issues']:
        label = json.dumps(item.get('reference'), ensure_ascii=False) if 'reference' in item else 'entrada rechazada'
        lines.append(f"- `{item['code']}` · {label}: {item['message']}")
        if 'expected_sha256' in item:
            lines.append(f"  SHA-256 previo: `{item['expected_sha256']}`; actual: `{item['current_sha256']}`.")
    lines.extend(['', '## Alcance', '', *('- ' + text for text in report['limits']), ''])
    return '\n'.join(lines)


def write_report(report, destination, package_path):
    """Exclusive report creation; identical reruns may reuse bytes, edits are preserved."""
    output = safe_path(destination, output=True)
    package = safe_path(package_path, output=True)
    if (output.is_relative_to(package) or output.suffix not in {'.json', '.md'}
            or output.name in {'inventory.json', 'queue.json', 'state.json'}):
        raise ValueError('Usa un informe JSON/MD fuera del paquete.')
    protected = PUBLIC_SOURCES | DECISION_EVIDENCE | {row['reference'] for row in report['sources']}
    if str(output.relative_to(ROOT)) in protected:
        raise ValueError('El informe no puede reemplazar una fuente.')
    raw = encoded(report) if output.suffix == '.json' else render(report).encode('utf-8')
    if output.exists():
        if output.is_file() and output.read_bytes() == raw:
            return 'unchanged'
        raise ValueError('El informe existente cambió; usa una salida nueva. No se sobrescriben notas.')
    output.parent.mkdir(parents=True, exist_ok=True)
    safe_path(output, output=True)
    with output.open('xb') as handle:
        handle.write(raw)
    return 'written'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Informe nuevo .json o .md dentro de reports/.')
    parser.add_argument('--format', choices=('json', 'md'), default='json', help='Formato de stdout.')
    args = parser.parse_args(argv)
    if args.output:
        safe_path(args.output, output=True)
    report = inspect_package(args.package)
    if args.output:
        write_report(report, args.output, args.package)
    else:
        print(encoded(report).decode('utf-8'), end='') if args.format == 'json' else print(render(report), end='')
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
