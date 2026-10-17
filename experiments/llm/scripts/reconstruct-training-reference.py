"""Reconstruye la referencia histórica; verifica hashes antes de escribir.

Solo lee el corpus, el tokenizador y el checkpoint local con weights_only=True.
No prepara el corpus actual, no modifica pesos y no ejecuta entrenamiento.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from nahuatl_local.passages import AXOLOTL, passage_id, records  # noqa: E402
from nahuatl_local.text import squash, strip_marks  # noqa: E402


def legacy_canonical(value):
    """Clave histórica de deduplicación de la corrida reconstruida (anterior a nah-ortho-1)."""
    return squash(re.sub(r'[^\w\s]', ' ', strip_marks(value.lower())))


def reconstruct():
    rows, seen_es, seen_nah = [], set(), set()
    for line, fields in records(ROOT / AXOLOTL):
        if len(fields) < 5:
            continue
        es, nah, variant, doc, iso = fields[:5]
        if (variant, iso) != ('Classical Nahuatl', 'nci'):
            continue
        es, nah = es.strip(), nah.strip()
        if not es or not nah or not doc.strip() or '\ufffd' in es + nah:
            continue
        if not 2 <= len(es.split()) <= 100 or not 2 <= len(nah.split()) <= 100:
            continue
        e, n = legacy_canonical(es), legacy_canonical(nah)
        if e == n or e in seen_es or n in seen_nah:
            continue
        seen_es.add(e)
        seen_nah.add(n)
        rows.append(dict(id=passage_id(line), es=es, nah=nah,
            variant=variant, iso='nci', document=doc,
            group='Chimalpahin: las ocho relaciones' if 'Libro las ocho relaciones' in doc else doc,
            locator=f'axolotl.csv, fila {line} (sin página de edición disponible)',
            source_url='https://www.axolotl-corpus.mx/',
            declared_license='MPL-2.0 (repositorio distribuidor)',
            linguistic_review='upstream_alignment_not_independently_reviewed'))
    groups = sorted({r['group'] for r in rows})
    random.Random(42).shuffle(groups)
    n = max(1, round(len(groups) * .15))
    test, valid = set(groups[:n]), set(groups[n:2*n])
    buckets = {k: [] for k in ('train', 'validation', 'test')}
    for r in rows:
        buckets['test' if r['group'] in test else 'validation' if r['group'] in valid else 'train'].append(r)
    return buckets


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True, help='Directorio nuevo; no se sobrescribe.')
    a = p.parse_args()
    if a.output.exists():
        p.error('Usa un directorio nuevo.')
    expected = json.loads((ROOT / 'outputs/continued-unseen/automation.json').read_text())['dataset_sha256']
    buckets = reconstruct()
    content = {k: ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows).encode('utf-8') for k, rows in buckets.items()}
    if any(hashlib.sha256(raw).hexdigest() != expected[k] for k, raw in content.items()):
        raise ValueError('La reconstrucción no coincide con la corrida. No se escribe nada.')
    import torch
    from transformers import AutoTokenizer
    from experiments.llm.runtime import encode_pair
    checkpoint = ROOT / 'outputs/continued-unseen/run/last/state.pt'
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    config = state['report']['config']
    tokenizer = AutoTokenizer.from_pretrained(str(ROOT / config['base_model']), local_files_only=True, trust_remote_code=False)
    usable = [r for r in buckets['train'] if encode_pair(tokenizer, r, config['max_length']) is not None]
    order, cursor = state['order'], state['cursor']
    if (sorted(order) != list(range(len(usable))) or len(usable) != 1759 or cursor != 650
            or state['step'] != 250 or config['gradient_accumulation'] != 1
            or state['report'].get('inherited_cursor') != 400
            or state['report'].get('best_step') != state['step']
            or any(state['report']['dataset_sha256'].get(k) != expected[k] for k in ('train', 'validation'))):
        raise ValueError('Checkpoint incompatible con la referencia histórica; no se escribe nada.')
    seen = dict(ids=[usable[i]['id'] for i in order[:cursor]], cursor=cursor,
        step=state['step'], initial_steps=state['report']['inherited_cursor'],
        usable_ids=[r['id'] for r in usable])
    manifest = dict(schema_version=1, method='legacy-preparation-reconstruction-hash-verified',
        dataset_sha256=expected,
        raw_sha256=hashlib.sha256((ROOT / AXOLOTL).read_bytes()).hexdigest(),
        adapter='outputs/continued-unseen/run/best', seen_pairs=cursor, usable_pairs=len(usable),
        prepared_train=len(buckets['train']),
        checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        notes='JSONL históricos exactos verificados por SHA256. IDs recorridos recuperados del orden y cursor del checkpoint local; sin entrenamiento.')
    a.output.mkdir(parents=True)
    for k, raw in content.items():
        (a.output / f'{k}.jsonl').write_bytes(raw)
    for k, value in (('seen', seen), ('manifest', manifest)):
        (a.output / f'{k}.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: len(v) for k, v in buckets.items()} | {'seen': cursor}, ensure_ascii=False))


if __name__ == '__main__':
    main()
