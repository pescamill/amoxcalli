import hashlib
import json
import time
import unittest

from nahuatl_local import spelling as S
from nahuatl_local import spelling_evaluation as E
from nahuatl_local.terms import TermIndex

_SEARCH = None


def search():
    global _SEARCH
    if _SEARCH is None:
        _SEARCH = S.Search(TermIndex())
        _SEARCH._build()
    return _SEARCH


class ProfileTests(unittest.TestCase):
    def test_converter_shows_each_profile(self):
        forms = {c['profile']: c['form'] for c in S.convert('cuauhtli')}
        self.assertEqual(forms['colonial'], 'quauhtli')
        self.assertEqual(forms['ack'], 'cuauhtli')
        self.assertEqual(forms['sep'], 'kwawtli')

    def test_saltillo_and_length_only_when_the_spelling_marks_them(self):
        conv = {c['profile']: c for c in S.convert('tlahtōlli')}
        self.assertEqual(conv['colonial']['form'], 'tlatolli')
        self.assertEqual(conv['ack']['form'], 'tlahtōlli')
        self.assertIsNone(conv['ack']['note'])
        plain = {c['profile']: c for c in S.convert('tlatolli')}
        self.assertIn('sin saltillo', plain['ack']['note'])
        self.assertIn('vocales largas', S.LIMIT_NOTE)

    def test_rules_apply_in_context_and_both_ways(self):
        alts = S.alternates(S.symbols(S.pivot('kuautli')))
        self.assertIn(S.symbols(S.pivot('cuauhtli')), alts)
        self.assertEqual(alts[S.symbols(S.pivot('cuauhtli'))][1], ('coda_w',))
        self.assertIn(S.symbols(S.pivot('xochitl')), S.alternates(S.symbols(S.pivot('xochit'))))
        # z = tz solo ante consonante
        self.assertNotIn(S.symbols(S.pivot('tzan')), S.alternates(S.symbols(S.pivot('zan'))))

    def test_distance_is_cheap_for_known_orthographic_changes(self):
        self.assertLess(S.distance('mesλi', 'meʦλi'), S.distance('kali', 'qali'))
        self.assertLess(S.distance('xočiλ', 'sočiλ'), 1)


class SearchTests(unittest.TestCase):
    def test_the_four_spellings_of_cualli_lead_to_cualli_with_sources(self):
        for q in ('kuali', 'kualli', 'qualli', 'cuali'):
            r = search().search(q)
            top = r['candidates'][0]
            self.assertEqual(top['lemma'], 'cualli', q)
            self.assertTrue(top['total'] > 0 and top['example'] and top['by_variety'], q)
            self.assertNotIn('calli', {v['form'] for v in top['spellings']})

    def test_a_conjecture_is_never_presented_as_attested(self):
        r = search().search('kuautli')
        self.assertFalse(r['attested'])
        self.assertIn('no aparece tal cual', r['note'])
        top = r['candidates'][0]
        self.assertEqual(top['lemma'], 'cuauhtli')
        self.assertNotEqual(top['match']['form'], 'kuautli')
        self.assertEqual(top['match']['how'], 'rule')
        self.assertIn('coda', top['match']['why'] + top['match']['rules'][0]['label'])

    def test_each_candidate_says_why_and_how_sure(self):
        for c in search().search('sochitl')['candidates']:
            self.assertTrue(c['match']['why'])
            self.assertIn(c['match']['confidence']['label'], ('alta', 'media', 'baja'))

    def test_fast_enough_for_suggestions_while_typing(self):
        s = search()
        start = time.perf_counter()
        for q in ('k', 'ku', 'kua', 'kual', 'kuali', 'huitzilopochtly', 'tlaltikpak', 'xochilt'):
            try:
                s.search(q)
            except ValueError:
                pass
        self.assertLess((time.perf_counter() - start) / 8, 0.1)

    def test_detail_view(self):
        gid = search().search('cualli')['candidates'][0]['id']
        d = search().detail(gid)
        self.assertTrue({'colonial', 'ack', 'sep'} <= {p['profile'] for p in d['profiles']})
        self.assertTrue(any(p['profile'] == 'azz' for p in d['profiles']))
        forms = {v['form'] for v in d['spellings']}
        self.assertTrue({'cualli', 'kuali', 'qualli', 'cuali'} <= forms)
        self.assertTrue(all(v['example'] for v in d['spellings'] if v['total']))


class GraphTests(unittest.TestCase):
    def test_edges_carry_type_and_evidence(self):
        g = search().graph
        self.assertTrue(g.edges)
        for e in list(g.edges.values())[:200]:
            self.assertTrue(e['types'] and e['status'] in ('certain', 'uncertain', 'rejected') and e['why'])

    def test_homographs_stay_apart(self):
        g = search().graph
        for a, b in (('cualli', 'calli'), ('cuahuitl', 'cahuitl'), ('cualli', 'tlacualli')):
            self.assertNotIn(S.pivot(b), g.cluster(S.pivot(a)))

    def test_human_reject_removes_an_edge_and_is_reversible(self):
        ti = search().terms
        from nahuatl_local.stems import es_tokens
        cfg = S.load_rules()
        base = S.Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=cfg, es_tokens=es_tokens)
        key = next(k for k, e in base.edges.items() if e['status'] == 'certain')
        a, b = base.surfaces(key[0])[0]['form'], base.surfaces(key[1])[0]['form']
        rejected = dict(cfg, decisions=cfg['decisions'] + [dict(a=a, b=b, decision='reject', by='prueba')])
        g = S.Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=rejected, es_tokens=es_tokens)
        self.assertEqual(g.edges[key]['status'], 'rejected')
        undone = dict(cfg, decisions=rejected['decisions'] + [dict(a=a, b=b, decision='clear', by='prueba')])
        g = S.Graph(ti.postings, ti.rows, ti.spelling_owner.keys(), cfg=undone, es_tokens=es_tokens)
        self.assertEqual(g.edges[key]['status'], 'certain')


class ReviewTests(unittest.TestCase):
    def test_decisions_are_appended_and_the_last_one_wins(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'editorial').mkdir()
            S.record_decision('mestli', 'metztli', 'reject', 'ana', root=tmp, when='2026-10-17T00:00:00+00:00')
            S.record_decision('mestli', 'metztli', 'clear', 'ana', root=tmp, when='2026-10-17T00:01:00+00:00')
            data = json.loads((Path(tmp) / S.REVIEW_PATH).read_text(encoding='utf-8'))
            self.assertEqual([d['decision'] for d in data['decisions']], ['reject', 'clear'])
            with self.assertRaises(ValueError):
                S.record_decision('cualli', 'kuali', 'accept', 'ana', root=tmp)  # misma forma pivote
            with self.assertRaises(ValueError):
                S.record_decision('a', 'b', 'borrar', 'ana', root=tmp)


class EvaluationTests(unittest.TestCase):
    def test_gold_set_is_frozen(self):
        digest = hashlib.sha256(E.GOLD.read_bytes()).hexdigest()
        self.assertEqual(digest, (E.GOLD.parent / 'spelling-search-v1.sha256').read_text().split()[0])
        gold = json.loads(E.GOLD.read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(gold['queries']), 100)

    def test_report_is_current(self):
        from nahuatl_local import evaluate_all
        report = E.evaluate(search())
        saved = json.loads(evaluate_all.REPORT.read_text(encoding='utf-8'))['spelling']
        self.assertEqual(evaluate_all.stable(saved), evaluate_all.stable(json.loads(json.dumps(report))), 'Regenera con make eval')
        self.assertEqual(report['summary']['all']['false_merges'], 0)

    def test_active_rules_passed_the_gate(self):
        cfg = json.loads((S.ROOT / S.RULES_PATH).read_text(encoding='utf-8'))
        decided = {t['rule']: t for t in cfg['trail']}
        for rid in cfg['active']:
            t = decided[rid]
            self.assertEqual(t['decision'], 'active')
            self.assertGreaterEqual(t['after']['pair_precision'], t['before']['pair_precision'])
            self.assertLessEqual(t['after']['false_merges'], t['before']['false_merges'])


if __name__ == '__main__':
    unittest.main()
