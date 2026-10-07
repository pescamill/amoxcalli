import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local.variant_audit import audit_corpus, apply_review, read_corpus, write_audit


class VariantAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / 'raw.csv'
        self.rows = [
            ['Sol, luna\ny cielo', 'Tonatiuh, metztli\nIlhuicatl', '', 'Diario', ''],
            ['La casa', 'in calli', '', 'Diario', ''],
            ['Los perros', 'in chichime', '', 'Revista', ''],
            ['El agua', 'in atl', 'Central Nahuatl', 'Otra obra', 'nhn'],
        ]
        with self.raw.open('w', encoding='utf-8', newline='') as file:
            csv.writer(file).writerows(self.rows)
        self.original = self.raw.read_bytes()
        self.proposals = self.root / 'proposals.json'
        self.proposals.write_text(json.dumps(dict(documents=[
            dict(document='Diario', proposed_variant='Classical Nahuatl', proposed_iso='nci',
                 scope='document', confidence='high', rationale='Identificación bibliográfica revisable.',
                 evidence=[dict(title='Fuente', url='https://example.org/diario', supports='Obra histórica.')]),
            dict(document='Revista', scope='row_review', rationale='Incluye textos distintos.'),
        ])), encoding='utf-8')
        self.report = audit_corpus(self.raw, self.proposals)
        self.output = self.root / 'audit'
        write_audit(self.report, self.output)
        self.audit = self.output / 'audit.json'
        self.review = self.output / 'review.csv'
        self.derived = self.root / 'derived.csv'

    def edit_review(self, **changes):
        with self.review.open(encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            fields, decisions = reader.fieldnames, list(reader)
        for title, values in changes.items():
            next(d for d in decisions if d['document'] == title).update(values)
        with self.review.open('w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(decisions)

    def test_audit_counts_records_not_physical_lines_and_changes_nothing(self):
        self.assertEqual(self.report['records'], 4)
        self.assertEqual(self.report['missing_labels'], 3)
        self.assertEqual(self.report['proposed_rows'], 2)
        self.assertEqual(self.report['unresolved_rows'], 1)
        self.assertEqual(self.report['source_sha256'], hashlib.sha256(self.original).hexdigest())
        self.assertEqual([r['id'] for r in self.report['rows']], ['axolotl-00001', 'axolotl-00002', 'axolotl-00003'])
        self.assertTrue(all(r['decision'] == 'pending' for r in self.report['rows']))
        self.assertEqual(self.raw.read_bytes(), self.original)

    def test_pending_review_creates_no_derived_file(self):
        with self.assertRaisesRegex(ValueError, 'No hay propuestas aprobadas'):
            apply_review(self.raw, self.audit, self.review, self.derived)
        self.assertFalse(self.derived.exists())

    def test_apply_changes_only_approved_empty_labels_and_preserves_original(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'))
        manifest = apply_review(self.raw, self.audit, self.review, self.derived)
        _, derived = read_corpus(self.derived)
        expected = [list(row) for row in self.rows]
        for row in expected[:2]:
            row[2], row[4] = 'Classical Nahuatl', 'nci'
        self.assertEqual(derived, expected)
        self.assertEqual(self.raw.read_bytes(), self.original)
        self.assertEqual(manifest['changed_rows'], 2)
        self.assertFalse(manifest['training_splits_changed'])
        self.assertTrue(all(c['reviewer'] == 'Responsable' and c['evidence'] for c in manifest['changes']))

    def test_reject_stale_corpus_before_writing(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'))
        self.raw.write_bytes(self.original + b'\n')
        with self.assertRaises(ValueError):
            apply_review(self.raw, self.audit, self.review, self.derived)
        self.assertFalse(self.derived.exists())

    def test_cannot_approve_mixed_source(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'),
                         Revista=dict(decision='approve', reviewer='Responsable', proposed_iso='nci',
                                      proposed_variant='Classical Nahuatl'))
        with self.assertRaisesRegex(ValueError, 'revisión individual'):
            apply_review(self.raw, self.audit, self.review, self.derived)
        self.assertFalse(self.derived.exists())

    def test_reviewer_required(self):
        self.edit_review(Diario=dict(decision='approve'))
        with self.assertRaisesRegex(ValueError, 'responsable'):
            apply_review(self.raw, self.audit, self.review, self.derived)

    def test_cannot_change_candidate_label_without_new_evidence(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable', proposed_iso='nhn',
                                    proposed_variant='Central Nahuatl'))
        with self.assertRaisesRegex(ValueError, 'cambió la propuesta'):
            apply_review(self.raw, self.audit, self.review, self.derived)

    def test_fingerprint_and_complete_coverage_validated(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'))
        report = json.loads(self.audit.read_text())
        report['rows'].pop()
        self.audit.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'cubre exactamente'):
            apply_review(self.raw, self.audit, self.review, self.derived)

    def test_cannot_overwrite_output(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'))
        self.derived.write_text('conservar')
        with self.assertRaisesRegex(ValueError, 'ruta de salida nueva'):
            apply_review(self.raw, self.audit, self.review, self.derived)
        self.assertEqual(self.derived.read_text(), 'conservar')

    def test_mismatched_id_cannot_enter_change_manifest(self):
        self.edit_review(Diario=dict(decision='approve', reviewer='Responsable'))
        report = json.loads(self.audit.read_text())
        report['rows'][0]['id'] = 'axolotl-09999'
        self.audit.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'identificador'):
            apply_review(self.raw, self.audit, self.review, self.derived)
        self.assertFalse(self.derived.exists())

    def test_global_proposal_rejected_for_existing_conflicting_labels(self):
        self.rows.append(['Otro pasaje', 'occe tlahtolli', 'Central Nahuatl', 'Diario', 'nhn'])
        with self.raw.open('w', encoding='utf-8', newline='') as file:
            csv.writer(file).writerows(self.rows)
        with self.assertRaisesRegex(ValueError, 'etiquetas existentes incompatibles'):
            audit_corpus(self.raw, self.proposals)

    def test_corpus_fixture_matches_known_total(self):
        report = audit_corpus(Path(__file__).resolve().parents[1] / 'corpus/axolotl/axolotl.csv')
        self.assertEqual((report['records'], report['missing_labels']), (16111, 2157))
        self.assertEqual(len(report['documents']), 8)
        self.assertFalse(report['complete_label_conflicts'])


if __name__ == '__main__':
    unittest.main()
