import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local.lexicon_candidates import candidates_csv, mine_candidates, write_candidates, written_tokens
from nahuatl_local.nahuatl_orthography import ORTHOGRAPHY_VERSION, storage


class LexiconCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / 'raw.csv'
        self.prepared = self.root / 'prepared'
        self.seed = self.root / 'seed.json'

    def put_rows(self, rows):
        with self.raw.open('w', encoding='utf-8', newline='') as file:
            csv.writer(file).writerows(rows)
        return self.raw.read_bytes()

    def mine(self, **kwargs):
        return mine_candidates(self.raw, self.prepared, self.seed, source_url='https://example.test/source', **kwargs)

    def test_original_labels_work_groups_and_frequency_are_required(self):
        self.put_rows([
            ['primera', 'tzapotl tzapotl', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['segunda', 'çapotl', 'Classical Nahuatl', 'Obra B', 'nci'],
            ['moderna', 'moderno moderno moderno', 'Central Nahuatl', 'Obra A', 'nhn'],
            ['pendiente', 'moderno moderno moderno', '', 'Diario', ''],
            ['discordante', 'moderno moderno moderno', 'Classical Nahuatl', 'Obra B', ''],
            ['relación', 'tlacayotl tlacayotl', 'Classical Nahuatl', 'Primera relación (Libro las ocho relaciones)', 'nci'],
            ['otra relación', 'tlacayotl', 'Classical Nahuatl', 'Quinta Relación (Libro las ocho relaciones)', 'nci'],
            ['escasa', 'citlalin', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['escasa', 'citlalin', 'Classical Nahuatl', 'Obra B', 'nci'],
        ])
        report = self.mine()
        self.assertEqual([c['comparison_form'] for c in report['candidates']], ['tzapotl'])
        candidate = report['candidates'][0]
        self.assertEqual((candidate['occurrences'], candidate['rows'], candidate['work_count']), (3, 2, 2))
        self.assertEqual({v['written'] for v in candidate['written_variants']}, {'çapotl', 'tzapotl'})
        self.assertEqual(report['counts']['rejected_records']['other_or_unknown_variant'], 3)

    def test_seed_exclusion_does_not_invent_lemmas_or_strip_prefixes(self):
        self.seed.write_text(json.dumps(dict(records=[dict(kind='form', written='tlālli')])), encoding='utf-8')
        self.put_rows([
            ['sin traducción de palabra', 'tlalli nitlalli nitlalli huel huel', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['contexto', 'Tlālli tlalli nitlalli huel', 'Classical Nahuatl', 'Obra B', 'nci'],
            ['contexto', 'uel uel', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['contexto', 'uel', 'Classical Nahuatl', 'Obra B', 'nci'],
        ])
        report = self.mine()
        self.assertEqual({c['comparison_form'] for c in report['candidates']}, {'nitlalli', 'huel', 'uel'})
        for candidate in report['candidates']:
            self.assertEqual(candidate['status'], 'candidate')
            self.assertIs(candidate['rights_training'], False)
            self.assertFalse({'lemma', 'definition', 'spanish_headword'} & candidate.keys())
        sheet = list(csv.DictReader(io.StringIO(candidates_csv(report))))
        self.assertTrue(all(row['spanish_definition'] == row['spanish_headword'] == row['reviewer'] == '' for row in sheet))

    def test_evidence_preserves_raw_text_logical_record_ids_and_distinct_works(self):
        original = self.put_rows([
            ['Contexto, con\nsalto', 'Tzapotl, çapotl\ntzapotl', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['segundo', 'çapotl', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['tercero', 'çapotl', 'Classical Nahuatl', 'Obra B', 'nci'],
            ['cuarto', 'tzapotl', 'Classical Nahuatl', 'Obra C', 'nci'],
            ['quinto', 'çapotl', 'Classical Nahuatl', 'Obra D', 'nci'],
        ])
        report = self.mine()
        candidate = report['candidates'][0]
        self.assertEqual(report['source']['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(report['normalization']['version'], ORTHOGRAPHY_VERSION)
        self.assertEqual(len(candidate['evidence']), 3)
        self.assertEqual(len({e['work_group'] for e in candidate['evidence']}), 3)
        first = candidate['evidence'][0]
        self.assertEqual((first['id'], first['record']), ('axolotl-00001', 1))
        self.assertEqual(first['es'], 'Contexto, con\nsalto')
        self.assertEqual(first['nah'], 'Tzapotl, çapotl\ntzapotl')
        self.assertEqual(candidate['evidence_ids'], [f'axolotl-{i:05d}' for i in range(1, 6)])
        for example in candidate['evidence']:
            self.assertEqual(example['source_url'], 'https://example.test/source')
            for token in example['tokens']:
                self.assertEqual(example['nah'][token['start']:token['end']], token['written'])
        self.assertEqual(self.raw.read_bytes(), original)

    def test_prepared_membership_protects_rejected_rows_in_heldout_works(self):
        rows = [
            ['contexto A', 'tzapotl tzapotl', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['contexto B', 'çapotl', 'Classical Nahuatl', 'Obra B', 'nci'],
            ['sin preparar', 'tzapotl', 'Classical Nahuatl', 'Obra B', 'nci'],
        ]
        original = self.put_rows(rows)
        self.prepared.mkdir()
        (self.prepared / 'manifest.json').write_text(json.dumps(dict(raw_sha256=hashlib.sha256(original).hexdigest())))
        for split, number in [('train', 1), ('test', 2)]:
            row = rows[number - 1]
            prepared = dict(id=f'axolotl-{number:05d}', es=storage(row[0]), nah=storage(row[1]), document=row[3])
            (self.prepared / f'{split}.jsonl').write_text(json.dumps(prepared) + '\n')
        (self.prepared / 'validation.jsonl').write_text('')
        report = self.mine()
        candidate = report['candidates'][0]
        self.assertEqual(candidate['prepared_split_distribution']['train']['occurrences'], 2)
        self.assertEqual(candidate['prepared_split_distribution']['test']['occurrences'], 1)
        self.assertEqual(candidate['prepared_split_distribution']['unprepared']['occurrences'], 1)
        self.assertEqual(candidate['heldout_work_groups'], ['Obra B'])
        self.assertTrue(candidate['contains_heldout_work'])
        reserved = next(e for e in candidate['evidence'] if e['document'] == 'Obra B')
        self.assertEqual((reserved['prepared_split'], reserved['work_split'], reserved['heldout']), ('test', 'test', True))

    def test_stale_prepared_hash_or_text_cannot_assign_membership(self):
        self.put_rows([['contexto', 'tzapotl', 'Classical Nahuatl', 'Obra A', 'nci']])
        self.prepared.mkdir()
        manifest = self.prepared / 'manifest.json'
        manifest.write_text(json.dumps(dict(raw_sha256='otra versión')))
        with self.assertRaisesRegex(ValueError, 'otro hash'):
            self.mine()
        manifest.write_text('{}')
        (self.prepared / 'train.jsonl').write_text(json.dumps(dict(id='axolotl-00001', es='otro texto', nah='tzapotl', document='Obra A')))
        with self.assertRaisesRegex(ValueError, 'no coincide'):
            self.mine()

    def test_one_work_cannot_be_marked_train_and_heldout(self):
        rows = [
            ['contexto A', 'tzapotl tzapotl', 'Classical Nahuatl', 'Obra  A', 'nci'],
            ['contexto B', 'çapotl', 'Classical Nahuatl', 'Obra  A', 'nci'],
        ]
        self.put_rows(rows)
        self.prepared.mkdir()
        for split, number in [('train', 1), ('test', 2)]:
            row = rows[number - 1]
            record = dict(id=f'axolotl-{number:05d}', es=storage(row[0]), nah=storage(row[1]), document=row[3])
            (self.prepared / f'{split}.jsonl').write_text(json.dumps(record) + '\n')
        with self.assertRaisesRegex(ValueError, 'más de un split'):
            self.mine()

    def test_rank_is_stable_and_output_cannot_overwrite_input(self):
        self.put_rows([
            ['a', 'zazanilli zazanilli tlahtolli tlahtolli', 'Classical Nahuatl', 'Obra A', 'nci'],
            ['b', 'zazanilli tlahtolli', 'Classical Nahuatl', 'Obra B', 'nci'],
        ])
        first, second = self.mine(limit=1), self.mine(limit=1)
        self.assertEqual(first, second)
        self.assertEqual(first['candidates'][0]['comparison_form'], 'tlahtolli')
        paths = write_candidates(first, self.root / 'inventory')
        self.assertEqual(json.loads(paths[0].read_text()), first)
        with paths[1].open(encoding='utf-8', newline='') as file:
            self.assertEqual(len(list(csv.DictReader(file))), 1)
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            write_candidates(first, self.root / 'inventory')
        self.assertEqual(write_candidates(first, self.root / 'inventory', overwrite=True), paths)
        with self.assertRaisesRegex(ValueError, 'sobrescribir'):
            write_candidates(first, self.raw.with_suffix(''))

    def test_word_extraction_does_not_create_hyphen_or_digit_fragments(self):
        text = 'Tlālli Tla\u0304lli ni-calli ni-\ncalli palabra123 quauh_tli 123 tlalli.'
        self.assertEqual([t[0] for t in written_tokens(text)], ['Tlālli', 'Tla\u0304lli', 'tlalli'])


if __name__ == '__main__':
    unittest.main()
