import unittest
from nahuatl_local.nahuatl_orthography import (
    storage, comparison, normalize, explain, audit,
    ORTHOGRAPHY_VERSION, STORAGE_RULE_IDS, COMPARISON_RULE_IDS,
)


class OrthographyTests(unittest.TestCase):
    def test_storage_idempotent(self):
        for text in ('Áéíóú Ç ñ ü', '  Auh  in ye\t yuhqui  ', 'e\u0301 nino\u0303', 'a\x91b'):
            self.assertEqual(storage(storage(text)), storage(text))

    def test_comparison_idempotent(self):
        for text in ('Tlahtōlli,', 'ÇVÑ', 'Auh in ye yuhqui', 'a\x94b'):
            self.assertEqual(comparison(comparison(text)), comparison(text))

    def test_storage_preserves_diacritics_cedilla_tilde_case(self):
        self.assertEqual(storage('Áéíóú Ç ñ ü'), 'Áéíóú Ç ñ ü')
        self.assertEqual(storage('Tlahtōlli'), 'Tlahtōlli')

    def test_nfc_composition(self):
        self.assertEqual(storage('e\u0301'), 'é')
        self.assertEqual(storage('n\u0303'), 'ñ')

    def test_c1_repair_maps_curly_quotes_and_drops_controls(self):
        self.assertEqual(storage('a\x91b'), 'a\u2018b')
        self.assertEqual(storage('a\x93b\x97c'), 'a\u201cb\u2014c')
        self.assertEqual(storage('a\x00b\x1fc'), 'abc')

    def test_comparison_collapses_variants(self):
        self.assertEqual(comparison('Tlahtōlli,'), comparison('tlahtolli'))
        self.assertEqual(comparison('Ç'), comparison('tz'))
        self.assertEqual(comparison('Ç'), 'tz')

    def test_comparison_v_to_u(self):
        self.assertEqual(comparison('auh v'), comparison('auh u'))

    def test_explain_records_changes(self):
        report = explain('Tlahtōlli,\x91', mode='comparison')
        self.assertTrue(report['changed'])
        self.assertNotEqual(report['output'], report['input'])
        self.assertEqual(report['mode'], 'comparison')
        fired = {r['id']: r['count'] for r in report['rules'] if r['count'] > 0}
        for expected in ('repair_c1', 'casefold', 'strip_marks', 'strip_punct'):
            self.assertIn(expected, fired)
        self.assertTrue(report['edits'])
        self.assertEqual(report['output'], comparison('Tlahtōlli,\x91'))

    def test_audit_aggregates_changes(self):
        report = audit(['Tlahtōlli,\x91', 'Ç', 'calli'], mode='comparison')
        self.assertEqual(report['mode'], 'comparison')
        self.assertEqual(report['total'], 3)
        self.assertGreaterEqual(report['changed'], 2)


class PendingRulesStayOffTests(unittest.TestCase):
    # Activarlas cambiaría claves de nah-ortho-1 y, con ellas, splits y cifras medidas.
    def test_pending_rules_are_defined_but_not_applied(self):
        for rule_id in ('glottal_h', 'qu_to_cu', 'initial_y'):
            self.assertNotIn(rule_id, COMPARISON_RULE_IDS)
        self.assertNotEqual(comparison('huel'), comparison('uel'))
        self.assertNotEqual(comparison('quauitl'), comparison('cuauitl'))


if __name__ == '__main__':
    unittest.main()
