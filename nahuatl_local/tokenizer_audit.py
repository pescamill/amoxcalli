"""Diagnóstico del tokenizador: fragmentación, fallback explícito y roundtrip.

Sin dependencias en tiempo de importación; ``transformers`` se carga solo dentro
de ``main()`` para poder auditar con un tokenizador falso en las pruebas.
"""
import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

BYTE_FALLBACK_WARN = 0.05
BYTE_TOKEN = re.compile(r'<0x[0-9A-Fa-f]{2}>')


def tokenizer_settings(tokenizer=None, path=None):
    """Lee la configuración sin incluir el vocabulario ni las fusiones BPE.

    La CLI usa el JSON local; los llamadores pueden usar el backend rápido.
    Una configuración ausente no demuestra que el fallback esté habilitado.
    """
    if path is not None:
        config = json.loads((Path(path) / 'tokenizer.json').read_text(encoding='utf-8'))
    else:
        backend = getattr(tokenizer, 'backend_tokenizer', None)
        config = json.loads(backend.to_str()) if backend is not None else {}
    model = {key: value for key, value in config.get('model', {}).items()
             if key not in ('vocab', 'merges')}
    return {'model': model, 'pre_tokenizer': config.get('pre_tokenizer'),
            'decoder': config.get('decoder'), 'normalizer': config.get('normalizer')}


def load_nahuatl_texts(path):
    """Extrae las frases en náhuatl clásico (nci) de un CSV de Axolotl."""
    texts = []
    for row in csv.reader(io.StringIO(Path(path).read_text(encoding='utf-8'))):
        if len(row) < 5:
            continue
        _, nah, variant, _, iso = row[:5]
        if variant != 'Classical Nahuatl' or iso != 'nci':
            continue
        nah = nah.strip()
        if nah:
            texts.append(nah)
    return texts


def audit_tokenizer(tokenizer, texts, sample=None, settings=None):
    """Estadísticas de tokenización. ``texts`` es cualquier iterable de cadenas."""
    texts = list(texts)
    if sample is not None:
        texts = texts[:sample]
    settings = tokenizer_settings(tokenizer) if settings is None else settings
    byte_fallback_enabled = settings.get('model', {}).get('byte_fallback')
    rows = chars = tokens = words = 0
    single_character_tokens = explicit_byte_tokens = unknown_token_tokens = 0
    unknown_id = getattr(tokenizer, 'unk_token_id', None)
    roundtrip_failures = 0
    non_ascii = Counter()
    char_count = Counter()
    for text in texts:
        rows += 1
        chars += len(text)
        words += len(text.split())
        non_ascii.update(c for c in text if ord(c) > 127)
        char_count.update(text)
        ids = tokenizer(text, add_special_tokens=False)['input_ids']
        tokens += len(ids)
        for token_id in ids:
            token = tokenizer.convert_ids_to_tokens(token_id)
            if isinstance(token, str):
                single_character_tokens += len(token) == 1
                explicit_byte_tokens += bool(BYTE_TOKEN.fullmatch(token))
            if unknown_id is not None and token_id == unknown_id:
                unknown_token_tokens += 1
        if tokenizer.decode(ids, skip_special_tokens=True) != text:
            roundtrip_failures += 1
    split_characters = []
    for char, count in char_count.items():
        if len(tokenizer(char, add_special_tokens=False)['input_ids']) > 1:
            split_characters.append({'char': char, 'codepoint': 'U+%04X' % ord(char), 'count': count})
    split_characters.sort(key=lambda entry: -entry['count'])
    # ByteLevel BPE usa caracteres visibles que representan bytes, incluso
    # letras ASCII normales. Su longitud no indica fallback. Sólo contamos
    # representaciones <0xHH> cuando el modelo declara byte_fallback=true.
    byte_fallback_tokens = explicit_byte_tokens if byte_fallback_enabled is True else 0 if byte_fallback_enabled is False else None
    byte_fallback_fraction = (byte_fallback_tokens / tokens if tokens else 0.0) if byte_fallback_tokens is not None else None
    reasons = []
    if byte_fallback_fraction is not None and byte_fallback_fraction > BYTE_FALLBACK_WARN:
        reasons.append('explicit_byte_fallback_above_threshold')
    if roundtrip_failures:
        reasons.append('roundtrip_failures')
    if unknown_token_tokens:
        reasons.append('unknown_token_tokens')
    return {
        'rows': rows,
        'chars': chars,
        'tokens': tokens,
        'tokens_per_char': round(tokens / chars, 4) if chars else 0.0,
        'tokens_per_word': round(tokens / words, 4) if words else 0.0,
        'tokenizer_settings': settings,
        'single_character_tokens': single_character_tokens,
        'single_character_token_fraction': round(single_character_tokens / tokens, 4) if tokens else 0.0,
        'explicit_byte_tokens': explicit_byte_tokens,
        'byte_fallback_enabled': byte_fallback_enabled,
        'byte_fallback_tokens': byte_fallback_tokens,
        'byte_fallback_fraction': round(byte_fallback_fraction, 4) if byte_fallback_fraction is not None else None,
        'split_character_inventory': split_characters,
        'unknown_token_tokens': unknown_token_tokens,
        'roundtrip_failures': roundtrip_failures,
        'non_ascii_inventory': dict(non_ascii.most_common()),
        'diagnostic_note': 'Los tokens de un solo carácter y los caracteres divididos en varios tokens describen fragmentación; no demuestran falta de cobertura. El fallback sólo se identifica por tokens <0xHH> con byte_fallback habilitado. Sin configuración, ese dato queda indeterminado.',
        'warning_reasons': reasons,
        'verdict': 'warn' if reasons else 'ok',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', required=True)
    p.add_argument('--tokenizer', default='models/base')
    p.add_argument('--output', default='reports/tokenizer-audit.json')
    a = p.parse_args()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(a.tokenizer, local_files_only=True, trust_remote_code=False)
    texts = load_nahuatl_texts(Path(a.data))
    report = audit_tokenizer(tokenizer, texts, settings=tokenizer_settings(path=a.tokenizer))
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
