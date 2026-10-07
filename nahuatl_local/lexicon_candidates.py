"""Inventario de concordancias para revisión; no crea lemas ni acepciones.

Cuenta únicamente filas con etiquetas originales Classical Nahuatl/nci. Las
formas de comparación agrupan grafías, conservando los tokens y pasajes
escritos. No segmenta morfemas ni utiliza propuestas de variantes pendientes.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import unicodedata
from pathlib import Path

from .data import ROOT, default_corpus_path, work_group
from .nahuatl_orthography import COMPARISON_RULE_IDS, ORTHOGRAPHY_VERSION, comparison, storage

VERSION = 'lexicon-candidates-1'
SPLITS = ('train', 'validation', 'test')
CSV_FIELDS = (
    'candidate_id', 'comparison_form', 'written_variants', 'occurrences',
    'rows', 'work_count', 'work_distribution', 'evidence_ids', 'example_ids',
    'source_url', 'prepared_split_distribution', 'heldout_work_groups',
    'status', 'rights_training', 'spanish_headword', 'spanish_definition',
    'reviewer', 'decision', 'notes',
)


def _sha256(value):
    return hashlib.sha256(value).hexdigest()


def written_tokens(text):
    """Extrae tokens alfabéticos con posiciones en el texto original.

    Se conservan marcas combinantes. Se omiten fragmentos adyacentes a cifras,
    guiones o apóstrofos: no se reconstruyen palabras partidas por OCR ni se
    convierten segmentos de una palabra en candidatos independientes.
    """
    start = None
    for position in range(len(text) + 1):
        char = text[position] if position < len(text) else ''
        letter = bool(char) and char.isalpha()
        mark = bool(char) and unicodedata.category(char).startswith('M')
        if letter or (mark and start is not None):
            if start is None:
                start = position
            continue
        if start is not None:
            before = text[start - 1] if start else ''
            after = char
            previous = start - 1
            while previous >= 0 and text[previous].isspace():
                previous -= 1
            continuation = previous >= 0 and text[previous] in '-‐‑'
            if not continuation and not any(c.isdigit() or c in "_-'’‐‑" for c in (before, after) if c):
                yield text[start:position], start, position
            start = None


def _seed_forms(path):
    path = Path(path)
    if not path.exists():
        return set(), dict(path=str(path.resolve()), present=False)
    raw = path.read_bytes()
    bundle = json.loads(raw)
    forms = {comparison(r['written']) for r in bundle.get('records', [])
             if r.get('kind') == 'form' and r.get('written')}
    return forms, dict(path=str(path.resolve()), present=True,
                       sha256=_sha256(raw), comparison_forms=sorted(forms))


def _prepared_membership(path, source_hash, rows):
    """Comprueba procedencia y conserva también la reserva de la obra completa."""
    path = Path(path)
    exact, groups, files = {}, {}, []
    manifest = path / 'manifest.json'
    if manifest.exists():
        raw_manifest = manifest.read_bytes()
        declared = json.loads(raw_manifest).get('raw_sha256')
        if declared and declared != source_hash:
            raise ValueError('El corpus preparado pertenece a otro hash de origen.')
        files.append(dict(path=str(manifest.resolve()), sha256=_sha256(raw_manifest)))
    for split in SPLITS:
        file = path / (split + '.jsonl')
        if not file.exists():
            continue
        raw = file.read_bytes()
        files.append(dict(path=str(file.resolve()), sha256=_sha256(raw)))
        for line in raw.decode('utf-8').splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            rid = record['id']
            original = rows.get(rid)
            if (original is None or original['document'] != record.get('document') or
                    any(storage(original[field]) != record.get(field) for field in ('es', 'nah'))):
                raise ValueError(f'El registro preparado {rid} no coincide con el CSV original.')
            if rid in exact:
                raise ValueError(f'El registro preparado {rid} aparece más de una vez.')
            group = work_group(original['document'])
            if group in groups and groups[group] != split:
                raise ValueError(f'La obra {group} aparece en más de un split preparado.')
            exact[rid], groups[group] = split, split
    present = [s for s in SPLITS if (path / (s + '.jsonl')).exists()]
    return exact, groups, dict(path=str(path.resolve()), files=files,
                              available_splits=present,
                              state='complete' if len(present) == 3 else 'partial' if present else 'unprepared')


def _source_url(raw_path):
    config = ROOT / 'configs/sources.json'
    try:
        known_corpus = default_corpus_path()
    except FileNotFoundError:
        known_corpus = None
    if known_corpus is not None and raw_path.resolve() == known_corpus.resolve() and config.exists():
        corpus = json.loads(config.read_text(encoding='utf-8'))['corpus']
        return f"https://github.com/{corpus['repository']}/blob/{corpus['revision']}/{corpus['path']}"
    return raw_path.resolve().as_uri()


def mine_candidates(raw_path, prepared_dir=ROOT / 'data/prepared', seed_path=ROOT / 'corpus/seed.json',
                    limit=100, min_occurrences=3, min_works=2, min_letters=2, source_url=None):
    """Genera candidatos documentados, conservando vacíos los campos editoriales."""
    if not 1 <= limit <= 100 or min_occurrences < 3 or min_works < 2 or min_letters < 2:
        raise ValueError('Usa límite 1–100, al menos 3 ocurrencias, 2 obras y 2 letras.')
    raw_path = Path(raw_path)
    raw = raw_path.read_bytes()
    source_hash = _sha256(raw)
    original, rejected = {}, collections.Counter()
    for number, fields in enumerate(csv.reader(io.StringIO(raw.decode('utf-8'), newline='')), 1):
        if len(fields) != 5:
            raise ValueError(f'El registro CSV {number} no contiene cinco campos.')
        es, nah, variant, document, iso = fields
        rid = f'axolotl-{number:05d}'
        original[rid] = dict(id=rid, record=number, es=es, nah=nah, variant=variant,
                             document=document, iso=iso)
    membership, group_splits, prepared = _prepared_membership(prepared_dir, source_hash, original)
    excluded, seed = _seed_forms(seed_path)
    url = source_url if source_url is not None else _source_url(raw_path)
    terms = {}
    accepted_rows = token_count = 0
    for rid, row in original.items():
        if (row['variant'], row['iso']) != ('Classical Nahuatl', 'nci'):
            rejected['other_or_unknown_variant'] += 1
            continue
        if not row['es'].strip() or not row['nah'].strip() or not row['document'].strip():
            rejected['empty'] += 1
            continue
        if '\ufffd' in row['es'] + row['nah']:
            rejected['replacement_character'] += 1
            continue
        accepted_rows += 1
        group = work_group(row['document'])
        row_tokens = collections.defaultdict(list)
        for written, start, end in written_tokens(row['nah']):
            key = comparison(written)
            if len(key) < min_letters or not key.isalpha():
                continue
            token_count += 1
            row_tokens[key].append(dict(written=written, start=start, end=end))
        for key, tokens in row_tokens.items():
            term = terms.setdefault(key, dict(forms=collections.Counter(), rows=[], works={}))
            term['forms'].update(t['written'] for t in tokens)
            exact_split = membership.get(rid, 'unprepared')
            work_split = group_splits.get(group, 'unprepared')
            evidence = dict(id=rid, record=row['record'], source_id='src-axolotl',
                            source_url=url, document=row['document'], work_group=group,
                            es=row['es'], nah=row['nah'], tokens=tokens,
                            prepared_split=exact_split, work_split=work_split,
                            heldout=work_split in ('validation', 'test') if work_split != 'unprepared' else None,
                            alignment_status='upstream_alignment_not_independently_reviewed',
                            rights_training=False)
            term['rows'].append(evidence)
            term['works'].setdefault(group, []).append(evidence)
    eligible = []
    for key, term in terms.items():
        count = sum(term['forms'].values())
        if key in excluded or count < min_occurrences or len(term['works']) < min_works:
            continue
        eligible.append((key, count, term))
    eligible.sort(key=lambda item: (-item[1], item[0]))
    candidates = []
    for key, count, term in eligible[:limit]:
        work_counts = []
        for group, evidence in sorted(term['works'].items()):
            work_counts.append(dict(work_group=group, occurrences=sum(len(e['tokens']) for e in evidence),
                                    rows=len(evidence), documents=sorted({e['document'] for e in evidence}),
                                    work_split=group_splits.get(group, 'unprepared')))
        ranked_works = sorted(work_counts, key=lambda w: (-w['occurrences'], w['work_group']))
        examples = [term['works'][w['work_group']][0] for w in ranked_works[:3]]
        split_counts = collections.defaultdict(lambda: dict(occurrences=0, rows=0))
        for evidence in term['rows']:
            tally = split_counts[evidence['prepared_split']]
            tally['rows'] += 1
            tally['occurrences'] += len(evidence['tokens'])
        heldout_works = [w['work_group'] for w in work_counts if w['work_split'] in ('validation', 'test')]
        candidates.append(dict(id='lexcand-' + _sha256(key.encode('utf-8'))[:16],
                               comparison_form=key,
                               written_variants=[dict(written=form, occurrences=n) for form, n in
                                                 sorted(term['forms'].items(), key=lambda item: (-item[1], item[0]))],
                               occurrences=count, rows=len(term['rows']), work_count=len(work_counts),
                               work_distribution=work_counts,
                               evidence_ids=[e['id'] for e in term['rows']], evidence=examples,
                               source_id='src-axolotl', source_url=url,
                               prepared_split_distribution=dict(sorted(split_counts.items())),
                               heldout_work_groups=heldout_works, contains_heldout_work=bool(heldout_works),
                               status='candidate', rights_training=False))
    return dict(version=VERSION, purpose='concordance_inventory_for_editorial_review',
                source=dict(path=str(raw_path.resolve()), sha256=source_hash,
                            source_id='src-axolotl', source_url=url),
                normalization=dict(version=ORTHOGRAPHY_VERSION, mode='comparison',
                                   rules=list(COMPARISON_RULE_IDS), written_text_preserved=True,
                                   morphology_segmented=False),
                criteria=dict(variant='Classical Nahuatl', iso='nci', min_occurrences=min_occurrences,
                              min_work_groups=min_works, min_letters=min_letters, limit=limit,
                              max_examples=3, examples_from_distinct_work_groups=True),
                seed_exclusions=seed, prepared_membership=prepared,
                counts=dict(source_records=len(original), known_classical_records=accepted_rows,
                            rejected_records=dict(rejected), counted_tokens=token_count,
                            comparison_groups=len(terms), excluded_seed_groups=sum(key in excluded for key in terms),
                            eligible_groups=len(eligible), exported_candidates=len(candidates)),
                status='candidate', rights_training=False,
                limitations=[
                    'Las grafías son tokens completos de concordancia, no lemas, raíces ni acepciones verificadas.',
                    'La forma de comparación puede agrupar formas distintas; conserva las grafías para revisión.',
                    'Las etiquetas originales y alineaciones bilingües no han sido verificadas por este inventario.',
                    'Los recuentos incluyen duplicados del archivo; dos work_group no demuestran fuentes históricas independientes.',
                    'El localizador corresponde a un registro CSV; la página de la edición primaria sigue pendiente.',
                    'Se conservan las reservas de validación y prueba por registro y obra; este inventario no se incorpora al entrenamiento.',
                    'Las propuestas pendientes de variante no se utilizan y no se asignan permisos nuevos de uso.',
                ], candidates=candidates)


def candidates_csv(report):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for candidate in report['candidates']:
        writer.writerow(dict(
            candidate_id=candidate['id'], comparison_form=candidate['comparison_form'],
            written_variants=json.dumps(candidate['written_variants'], ensure_ascii=False),
            occurrences=candidate['occurrences'], rows=candidate['rows'], work_count=candidate['work_count'],
            work_distribution=json.dumps(candidate['work_distribution'], ensure_ascii=False),
            evidence_ids=' | '.join(candidate['evidence_ids']),
            example_ids=' | '.join(e['id'] for e in candidate['evidence']),
            source_url=candidate['source_url'],
            prepared_split_distribution=json.dumps(candidate['prepared_split_distribution'], ensure_ascii=False),
            heldout_work_groups=' | '.join(candidate['heldout_work_groups']),
            status='candidate', rights_training='false', spanish_headword='', spanish_definition='',
            reviewer='', decision='', notes=''))
    return output.getvalue()


def write_candidates(report, output, csv_output=None, overwrite=False):
    output = Path(output)
    paths = (output.with_suffix('.json'), Path(csv_output) if csv_output is not None else output.with_suffix('.csv'))
    if paths[1].suffix.lower() != '.csv' or paths[0].resolve() == paths[1].resolve():
        raise ValueError('La salida CSV debe usar una ruta .csv distinta del JSON.')
    inputs = {Path(report['source']['path']).resolve(), Path(report['seed_exclusions']['path']).resolve()}
    inputs.update(Path(file['path']).resolve() for file in report['prepared_membership']['files'])
    inputs.add((ROOT / 'configs/sources.json').resolve())
    if any(path.resolve() in inputs for path in paths):
        raise ValueError('La salida no puede sobrescribir un archivo de entrada.')
    if not overwrite and any(path.exists() for path in paths):
        raise ValueError('La salida ya existe; usa rutas nuevas o --overwrite para regenerar el inventario.')
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    paths[1].write_text(candidates_csv(report), encoding='utf-8', newline='')
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--prepared', type=Path, default=ROOT / 'data/prepared')
    parser.add_argument('--seed', type=Path, default=ROOT / 'corpus/seed.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/lexicon-candidates.json')
    parser.add_argument('--csv', type=Path, help='Salida CSV; por defecto comparte el nombre del JSON.')
    parser.add_argument('--overwrite', action='store_true', help='Regenera archivos de inventario existentes.')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    report = mine_candidates(args.raw or default_corpus_path(), args.prepared, args.seed, args.limit)
    paths = write_candidates(report, args.output, args.csv, args.overwrite)
    print(json.dumps(dict(counts=report['counts'], files=[str(p) for p in paths]), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
