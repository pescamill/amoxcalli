"""Revisión determinista y ficha de evaluación humana, sin servicios externos."""
import unicodedata

from .text import squash


def exact(text):
    """Igualdad exacta salvo mayúsculas y espacios (conserva acentos)."""
    return squash(unicodedata.normalize('NFC', text).lower())


def request_bundle(result):
    return dict(schema_version=1, source_text=result['input'], candidate=result['text'],
                supporting_evidence=result.get('related_passages', []),
                glyph_evidence=result.get('glyph_evidence', []),
                review=local_review(result),
                human_review=dict(reviewer='', variant='', source_locator='',
                                  fidelity=None, historical_fit=None, notes=''))


def local_review(result):
    rows=result.get('related_passages',[]);candidate=exact(result['text']);source=exact(result['input'])
    matches=[r['id'] for r in rows if candidate and exact(r.get('nah',''))==candidate and exact(r.get('es',''))==source]
    return {'provider':'local_rules','calibrated':False,'exact_aligned_pair_ids':matches,'semantic_fidelity':None,'classical_nahuatl_fit':None,'modernization_risk':None,'decision':'attested_pair_needs_source_review' if matches else 'human_review','reason':'Coincidencia textual con un par del corpus; no verifica su edición ni alineación.' if matches else 'No hay prueba local suficiente para certificar esta traducción.','automatic_acceptance':False}


def validate_request(bundle):
    if bundle.get('schema_version') != 1 or not all(isinstance(bundle.get(k), str) for k in ('source_text', 'candidate')):
        raise ValueError('Ficha de revisión inválida')
    if not isinstance(bundle.get('supporting_evidence'), list) or not isinstance(bundle.get('human_review'), dict):
        raise ValueError('Faltan evidencia o campos de revisión humana')
    return bundle

