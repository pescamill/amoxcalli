"""Read-only candidate preflight and HUMAN inspection of visual development refs.

No model imports, weights, image requests, prompts, execution or training.
References never enter the existing public comparison/download projection.
"""
import argparse
import ast
import copy
import hashlib
from importlib import metadata
import json
from pathlib import Path

from .community import ROOT
from .documentary_evaluation import load_development, public_path

REGISTRY = 'transformers/models/auto/configuration_auto.py'
PACKAGES = ('torch', 'transformers', 'peft', 'mlx', 'mlx-vlm')
CANDIDATE = dict(model_id='Qwen/Qwen3-VL-4B-Instruct', model_type='qwen3_vl',
                 architecture='Qwen3VLForConditionalGeneration', status='not_run',
                 source_url='https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct',
                 config_revision='ebb281ec70b05090aa6165b016eac8ec08e71b17',
                 config_url='https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json',
                 config_evidence='Official configuration inspected by coordinator; not fetched at runtime.',
                 weights_installation='not_registered_for_candidate', weights_loaded=False, model_calls=0,
                 training=False, images_processed=0, metrics=None, cost=None)
NEXT_TASK = ('Tras autorización de fase y derechos explícitos: disponer de pesos y runtime compatible, '
             'hacer una prueba de carga y una inferencia local sobre una imagen de prueba admitida, '
             'registrar salida, tiempo y memoria reales. Definir otra referencia para reconocer píxeles; '
             'estas preguntas documentales necesitan catálogo y no son una prueba image-only.')


def registered_architectures(path):
    """Inspect a literal registry with AST; never import/execute package code."""
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Aliased package registry.')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CONFIG_MAPPING_NAMES' for t in node.targets):
            value = node.value
            if (not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name)
                    or value.func.id != 'OrderedDict' or len(value.args) != 1 or value.keywords):
                raise ValueError('Nonliteral registry.')
            pairs = ast.literal_eval(value.args[0])
            if not isinstance(pairs, list) or not all(isinstance(p, tuple) and len(p) == 2
                                                    and all(isinstance(v, str) for v in p) for p in pairs):
                raise ValueError('Invalid registry entries.')
            return {key for key, _ in pairs}
    raise ValueError('Registry missing.')


def preflight():
    packages, distributions = {}, {}
    for name in PACKAGES:
        try:
            distribution = metadata.distribution(name)
            distributions[name] = distribution
            packages[name] = dict(installed=True, version=distribution.version)
        except metadata.PackageNotFoundError:
            packages[name] = dict(installed=False, version=None)
    registration = dict(status='missing_package', qwen3_vl=None, qwen3=None)
    if 'transformers' in distributions:
        try:
            names = registered_architectures(distributions['transformers'].locate_file(REGISTRY))
            registration = dict(status='checked_literal_registry', qwen3_vl='qwen3_vl' in names, qwen3='qwen3' in names)
        except (OSError, SyntaxError, ValueError, TypeError):
            registration['status'] = 'registry_unreadable'
    state = ('architecture_missing' if registration['qwen3_vl'] is False else
             'metadata_ready_inference_unverified' if registration['qwen3_vl'] is True and packages['torch']['installed'] else
             'dependencies_or_registry_pending')
    return dict(packages=packages, registration=registration, state=state,
                method='package_metadata_and_literal_AST_only', inference_verified=False,
                hardware_fit_verified=False, automatic_upgrade=False)


def _snapshot(root, include_cases):
    result = dict(schema_version=1, kind='visual_documentary_preparation', split='development',
                  candidate=copy.deepcopy(CANDIDATE), preflight=preflight(),
                  execution_enabled=False, available=False, case_count=0,
                  scope='documentary_reference_inspection_not_pixel_benchmark',
                  review_status='source_derived_not_human_validated', next_task=NEXT_TASK,
                  review_url='/api/laboratory/visual-preparation', validation_errors=[])
    if include_cases:
        result['cases'] = []
    try:
        queries = load_development(modality='visual', root=root)
        if any(q['split'] != 'development' or q['modality'] != 'visual' for q in queries):
            raise ValueError('Development visual only.')
        if include_cases:
            raw = public_path(Path(root), 'corpus/pictography/catalog.json').read_bytes()
            if any(q['source_hashes'].get('corpus/pictography/catalog.json') != hashlib.sha256(raw).hexdigest() for q in queries):
                raise ValueError('Catalog changed during projection.')
            documents = {d['id']: d for d in json.loads(raw)['documents']}
            for q in queries:
                reference = copy.deepcopy(q['reference'])
                document = next(documents[rid] for rid in reference['source_ids'] if rid in documents)
                images = sorted({f['value'] for f in reference['fields'] if f['field'] == 'image'})
                result['cases'].append(dict(id=q['id'], question=q['question'],
                    document={k: document[k] for k in ('id', 'title', 'url', 'attribution')},
                    split=q['split'], modality=q['modality'], review_status=q['review_status'],
                    proposed_input=dict(question=q['question'], image_reference_urls=images,
                                        catalog_page_url=document['url']),
                    reference=reference, rights=copy.deepcopy(q['rights']),
                    source_hashes=copy.deepcopy(q['source_hashes']), uncertainty=q['uncertainty']))
        result.update(available=True, case_count=len(queries))
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        result['validation_errors'] = ['development_battery_or_sources_invalid']
        if include_cases:
            result['cases'] = []
    return result


def status(root=ROOT):
    """Public status/counts only: never include expected fields in snapshots."""
    return _snapshot(root, False)


def review(root=ROOT):
    """Explicit HUMAN reference inspection, separate from public downloads."""
    return _snapshot(root, True)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(preflight(), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
