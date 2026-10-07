"""Audita variantes sin modificar el original; aplica solo decisiones revisadas.

Las propuestas bibliográficas no son etiquetas verificadas ni permisos de uso.
La aplicación produce un CSV nuevo y no modifica los splits de entrenamiento.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path

from .data import ROOT, default_corpus_path

VERSION = 'variant-audit-1'
VARIANTS = {
    'nci': 'Classical Nahuatl', 'nhn': 'Central Nahuatl',
    'azz': 'Highland Puebla Nahuatl', 'nhm': 'Morelos Nahuatl',
    'nhw': 'Western Huasteca Nahuatl', 'nhe': 'Eastern Huasteca Nahuatl',
}
REVIEW_FIELDS = ['document', 'source_sha256', 'row_count', 'proposed_variant',
                 'proposed_iso', 'evidence_urls', 'rationale', 'decision',
                 'reviewer', 'notes']


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def read_corpus(path):
    raw = Path(path).read_bytes()
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8'), newline='')))
    invalid = [i for i, row in enumerate(rows, 1) if len(row) != 5]
    if invalid:
        raise ValueError(f'Registros con esquema distinto de cinco campos: {invalid[:10]}')
    return raw, rows


def row_fingerprint(row):
    return sha256(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def missing_label(row):
    return not row[2].strip() or not row[4].strip()


def audit_corpus(raw_path, proposals_path=None):
    raw, rows = read_corpus(raw_path)
    bundle = json.loads(Path(proposals_path).read_text(encoding='utf-8')) if proposals_path else {}
    proposals = bundle.get('documents', [])
    if len({p['document'] for p in proposals}) != len(proposals):
        raise ValueError('La propuesta contiene títulos repetidos.')
    by_document = {p['document']: p for p in proposals}
    groups = collections.defaultdict(list)
    conflicts = []
    for number, row in enumerate(rows, 1):
        if missing_label(row):
            groups[row[3]].append((number, row))
        elif row[4] not in VARIANTS or VARIANTS[row[4]] != row[2]:
            conflicts.append(dict(id=f'axolotl-{number:05d}', variant=row[2], iso=row[4]))
    documents = []
    pending = []
    for title, items in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        proposal = by_document.get(title, {})
        iso = proposal.get('proposed_iso', '')
        variant = proposal.get('proposed_variant', '')
        if iso and VARIANTS.get(iso) != variant:
            raise ValueError(f'Variante e ISO incompatibles en la propuesta: {title}')
        scope = proposal.get('scope', 'row_review')
        evidence = proposal.get('evidence', [])
        if iso and (scope != 'document' or not evidence):
            raise ValueError(f'Una propuesta global requiere evidencia y alcance document: {title}')
        existing_labels = collections.Counter((r[2], r[4]) for r in rows
                                             if r[3] == title and not missing_label(r))
        if iso and any(label != (variant, iso) for label in existing_labels):
            raise ValueError(f'La obra tiene etiquetas existentes incompatibles; requiere revisión individual: {title}')
        document = dict(document=title, rows=len(items), scope=scope,
                        proposed_variant=variant, proposed_iso=iso,
                        confidence=proposal.get('confidence', 'unresolved'),
                        rationale=proposal.get('rationale', 'Fuente y variante pendientes de identificación.'),
                        evidence=evidence, caveats=proposal.get('caveats', []),
                        existing_labels=[dict(variant=v, iso=i, rows=n)
                                         for (v, i), n in sorted(existing_labels.items())],
                        decision='pending',
                        samples=[dict(id=f'axolotl-{number:05d}', es=row[0], nah=row[1])
                                 for number, row in items[:3]])
        documents.append(document)
        for number, row in items:
            pending.append(dict(id=f'axolotl-{number:05d}', record=number, document=title,
                                original_variant=row[2], original_iso=row[4],
                                row_sha256=row_fingerprint(row),
                                proposed_variant=variant, proposed_iso=iso,
                                decision='pending'))
    return dict(version=VERSION, source=str(Path(raw_path).resolve()), source_sha256=sha256(raw),
                records=len(rows), missing_labels=len(pending),
                complete_label_conflicts=conflicts,
                proposed_rows=sum(d['rows'] for d in documents if d['proposed_iso']),
                unresolved_rows=sum(d['rows'] for d in documents if not d['proposed_iso']),
                proposals_sha256=sha256(Path(proposals_path).read_bytes()) if proposals_path else None,
                research_date=bundle.get('research_date'), documents=documents, rows=pending,
                limitations=[
                    'Identificar una obra no verifica cada alineación, página o traducción.',
                    'El título de una revista o antología no identifica necesariamente una sola variedad.',
                    'Las propuestas no cambian el original, el archivo consultable ni los splits preparados.',
                    'La clasificación lingüística no autoriza redistribución ni entrenamiento.',
                ])


def review_sheet(report):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDS)
    writer.writeheader()
    for document in report['documents']:
        writer.writerow(dict(document=document['document'], source_sha256=report['source_sha256'],
                             row_count=document['rows'], proposed_variant=document['proposed_variant'],
                             proposed_iso=document['proposed_iso'],
                             evidence_urls=' | '.join(e['url'] for e in document['evidence']),
                             rationale=document['rationale'], decision='pending', reviewer='', notes=''))
    return stream.getvalue()


def markdown_report(report):
    lines = ['# Auditoría de variantes de Axolotl', '',
             f"Registros: **{report['records']:,}**. Sin etiqueta completa: **{report['missing_labels']:,}**.", '',
             f"Filas con propuesta bibliográfica: **{report['proposed_rows']:,}**; pendientes de identificación o revisión individual: **{report['unresolved_rows']:,}**.", '',
             'Todas las decisiones siguen pendientes. El CSV original y los splits preparados se conservan.', '',
             '| Obra | Filas | Propuesta ISO | Alcance |', '|---|---:|---|---|']
    for d in report['documents']:
        title = (d['document'] or 'Sin título').replace('|', '\\|')
        lines.append(f"| {title} | {d['rows']} | {d['proposed_iso'] or 'Pendiente'} | {d['scope']} |")
    for d in report['documents']:
        lines += ['', '## ' + (d['document'] or 'Sin título'), '', d['rationale'], '']
        for e in d['evidence']:
            lines.append(f"- [{e['title']}]({e['url']}): {e['supports']}")
        if d['caveats']:
            lines += ['', 'Límites: ' + ' '.join(d['caveats'])]
        lines += ['', 'Muestras del CSV (no cotejadas contra cada página):', '']
        for sample in d['samples']:
            lines += [f"- **{sample['id']}** — ES: {sample['es']} / NAH: {sample['nah']}"]
    lines += ['', '## Revisión y aplicación', '',
              'En `review.csv`, un responsable puede cambiar `pending` por `approve` o `reject` y completar `reviewer`. Solo las propuestas con alcance `document` pueden propagarse. Los grupos mixtos necesitan decisiones por registro en una auditoría posterior.', '',
              'La aplicación verifica el hash del corpus, los localizadores y los textos; produce un CSV derivado y un manifiesto. No incorpora filas al entrenamiento. Preparar un conjunto nuevo cambia el benchmark y exige revisar obras reservadas y derechos.', '',
              f"SHA-256 del original: `{report['source_sha256']}`", '']
    return '\n'.join(lines)


def write_audit(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / 'review.csv').write_text(review_sheet(report), encoding='utf-8', newline='')
    (output / 'README.md').write_text(markdown_report(report), encoding='utf-8')


def apply_review(raw_path, audit_path, review_path, output):
    """Crea una copia derivada tras validar todas las decisiones; nunca sobrescribe."""
    raw, rows = read_corpus(raw_path)
    audit = json.loads(Path(audit_path).read_text(encoding='utf-8'))
    if audit.get('version') != VERSION or audit.get('source_sha256') != sha256(raw):
        raise ValueError('El corpus o la versión cambió desde la auditoría.')
    if audit.get('records') != len(rows):
        raise ValueError('Número de registros incompatible con la auditoría.')
    audited_rows = {}
    for record in audit['rows']:
        number = record['record']
        if number in audited_rows or not 1 <= number <= len(rows):
            raise ValueError('Localizador duplicado o fuera de rango.')
        if record['id'] != f'axolotl-{number:05d}':
            raise ValueError('El identificador no corresponde al localizador auditado.')
        row = rows[number - 1]
        if row_fingerprint(row) != record['row_sha256'] or row[3] != record['document'] or not missing_label(row):
            raise ValueError(f"El registro {number} ya no coincide con la auditoría.")
        audited_rows[number] = record
    if set(audited_rows) != {i for i, row in enumerate(rows, 1) if missing_label(row)}:
        raise ValueError('La auditoría no cubre exactamente las etiquetas incompletas.')
    documents = {d['document']: d for d in audit['documents']}
    with Path(review_path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        if not set(REVIEW_FIELDS) <= set(reader.fieldnames or []):
            raise ValueError('Faltan columnas en la revisión.')
        decisions = list(reader)
    seen = set()
    approved = {}
    for decision in decisions:
        title = decision['document']
        if title in seen or title not in documents:
            raise ValueError('Título desconocido o repetido en la revisión.')
        seen.add(title)
        d = documents[title]
        if decision['source_sha256'] != audit['source_sha256'] or decision['row_count'] != str(d['rows']):
            raise ValueError(f'Hash o cantidad de filas incompatible: {title}')
        if decision['decision'] not in ('pending', 'approve', 'reject'):
            raise ValueError('Decisión inválida: usa pending, approve o reject.')
        if decision['decision'] != 'approve':
            continue
        if not decision['reviewer'].strip():
            raise ValueError('La aprobación requiere responsable de revisión.')
        if d['scope'] != 'document' or not d['proposed_iso'] or not d['evidence']:
            raise ValueError(f'Este grupo necesita identificación o revisión individual: {title}')
        if (decision['proposed_iso'], decision['proposed_variant']) != (d['proposed_iso'], d['proposed_variant']):
            raise ValueError('La revisión cambió la propuesta; genera una auditoría nueva con evidencia.')
        if VARIANTS.get(d['proposed_iso']) != d['proposed_variant']:
            raise ValueError('Variante e ISO incompatibles.')
        if any(r[3] == title and not missing_label(r) and
               (r[2], r[4]) != (d['proposed_variant'], d['proposed_iso']) for r in rows):
            raise ValueError('La obra tiene etiquetas existentes incompatibles; requiere revisión individual.')
        members = [record for record in audited_rows.values() if record['document'] == title]
        if len(members) != d['rows']:
            raise ValueError('La cantidad de filas del grupo no coincide.')
        if any(rows[r['record'] - 1][2].strip() or rows[r['record'] - 1][4].strip() for r in members):
            raise ValueError('No se propagan propuestas sobre etiquetas parcialmente existentes.')
        approved[title] = decision
    if not approved:
        raise ValueError('No hay propuestas aprobadas; no se creó ningún archivo.')
    changed = []
    for number, record in sorted(audited_rows.items()):
        title = record['document']
        if title not in approved:
            continue
        d = documents[title]
        rows[number - 1][2], rows[number - 1][4] = d['proposed_variant'], d['proposed_iso']
        changed.append(dict(id=record['id'], record=number, document=title,
                            variant=d['proposed_variant'], iso=d['proposed_iso'],
                            reviewer=approved[title]['reviewer'], notes=approved[title]['notes'],
                            rationale=d['rationale'], evidence=d['evidence']))
    output = Path(output)
    manifest_path = output.with_suffix(output.suffix + '.audit.json')
    if output.exists() or manifest_path.exists() or output.resolve() == Path(raw_path).resolve():
        raise ValueError('Usa una ruta de salida nueva; no se sobrescribe ningún archivo.')
    stream = io.StringIO(newline='')
    csv.writer(stream).writerows(rows)
    derived = stream.getvalue().encode('utf-8')
    manifest = dict(version=VERSION, source_sha256=sha256(raw), output_sha256=sha256(derived),
                    audit_sha256=sha256(Path(audit_path).read_bytes()),
                    review_sha256=sha256(Path(review_path).read_bytes()),
                    records=len(rows), changed_rows=len(changed), changes=changed,
                    rights='Sin cambio de permisos; la revisión lingüística no autoriza entrenamiento.',
                    training_splits_changed=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as file:
        file.write(derived)
    with manifest_path.open('x', encoding='utf-8') as file:
        file.write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    audit = commands.add_parser('audit')
    audit.add_argument('--raw', type=Path)
    audit.add_argument('--proposals', type=Path, default=ROOT / 'corpus/variant-proposals-v1.json')
    audit.add_argument('--output', type=Path, required=True)
    apply = commands.add_parser('apply')
    apply.add_argument('--raw', type=Path)
    apply.add_argument('--audit', type=Path, required=True)
    apply.add_argument('--review', type=Path, required=True)
    apply.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.raw or default_corpus_path()
    if args.command == 'audit':
        report = audit_corpus(raw, args.proposals)
        write_audit(report, args.output)
        print(json.dumps({k: report[k] for k in ('records', 'missing_labels', 'proposed_rows', 'unresolved_rows')}, indent=2))
    else:
        report = apply_review(raw, args.audit, args.review, args.output)
        print(json.dumps(dict(records=report['records'], changed_rows=report['changed_rows'], output=str(args.output)), indent=2))


if __name__ == '__main__':
    main()
