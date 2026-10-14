import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from nahuatl_local.morphology import Analyzer, Lexicon, phonemic_key, key_of, readable, PARTICLES
from nahuatl_local.stems import StemConcordance, GlossHints, WordStudy, es_tokens

ROOT = Path(__file__).resolve().parents[1]


def lexicon_records():
    rows = []
    for written, label, pos in [('calli', 'casa', 'noun'), ('itta', 'ver', 'verb'), ('xochitl', 'flor', 'noun'),
                                ('atl', 'agua', 'noun'), ('Aca', 'alguno.', 'other'),
                                ('Ic', 'con. preposicion.', 'other'), ('Nacatemi', 'mejorar la llaga. preterit: onacaten.', 'other')]:
        sid = 'sense-' + written.lower()
        rows.append(dict(id=sid, kind='sense', label=label, pos=pos))
        rows.append(dict(id='lex-' + written.lower(), kind='form', written=written, sense_id=sid, url='https://example.org/' + written))
    return rows


class PhonemicKeyTests(unittest.TestCase):
    def test_colonial_spellings_share_a_key(self):
        for group in (['yhuan', 'ihuan', 'iuan'], ['xihuitl', 'xiuitl'], ['huel', 'uel'],
                      ['iquac', 'yquac', 'ihcuac'], ['quauitl', 'cuahuitl'], ['çan', 'zan'], ['eecatl', 'ehecatl']):
            self.assertEqual(len({key_of(w) for w in group}), 1, group)

    def test_spans_preserve_source_spelling(self):
        key, spans = phonemic_key('NIQUITTA')
        self.assertEqual(key, 'nikitta')
        self.assertEqual(['NIQUITTA'[a:b] for a, b in spans], ['N', 'I', 'QU', 'I', 'T', 'T', 'A'])
        key, spans = phonemic_key('tlahtohuani')
        self.assertEqual(readable(key), 'tlatoani')
        self.assertEqual(''.join('tlahtohuani'[a:b] for a, b in spans), 'tlahtohuani')

    def test_particles_are_indexed_by_key(self):
        self.assertIn(key_of('yn'), PARTICLES)
        self.assertIn(key_of('yhuan'), PARTICLES)


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = Analyzer(lexicon_records())

    def seg(self, word):
        return self.a.analyze(word, limit=3)[0]['segmentation']

    def test_dictionary_backed_segmentations(self):
        self.assertEqual(self.seg('nocal'), 'no-cal')
        self.assertEqual(self.seg('calco'), 'cal-co')
        self.assertEqual(self.seg('niquitta'), 'ni-qu-itta')
        self.assertEqual(self.seg('NIQUITTA'), 'NI-QU-ITTA')
        self.assertEqual(self.seg('noxochiuh'), 'no-xochi-uh')
        self.assertEqual(self.seg('atl'), 'a-tl')

    def test_every_analysis_declares_its_basis_and_cites_entries(self):
        best = self.a.analyze('nocal')[0]
        self.assertEqual(best['basis'], 'dictionary')
        self.assertEqual(best['dictionary'][0]['sense_id'], 'sense-calli')
        self.assertTrue(best['dictionary'][0]['url'].startswith('https://'))
        self.assertTrue(all(a['note'] for a in self.a.analyze('chachalaca')))

    def test_function_words_and_category_mismatch_do_not_support_stems(self):
        # «Aca: alguno» no puede ser la raíz de un verbo con prefijo de objeto.
        best = self.a.analyze('quimaca')[0]
        self.assertFalse(any(d['written'] == 'Aca' for d in best['dictionary']))
        self.assertIn('Ic', [h['written'] for h in self.a.lexicon.whole[key_of('ic')]])

    def test_molina_preterit_is_registered_as_stem(self):
        self.assertTrue(self.a.lexicon.lookup(key_of('nacaten')))

    def test_allomorphy_constraints(self):
        segs = [a['segmentation'] for a in self.a.analyze('quimaca', limit=5)]
        self.assertNotIn('quim-aca', segs)  # quim- solo ante m/p

    def test_corpus_counts_resolve_unknown_stems(self):
        a = Analyzer(lexicon_records())
        a.fit(['quimaca', 'nechmaca', 'quimacaque', 'timaca', 'nimaca', 'tinechmaca', 'maca'])
        self.assertEqual(a.analyze('quimaca')[0]['segmentation'], 'qui-maca')
        self.assertEqual(a.analyze('quimaca')[0]['basis'], 'corpus')

    def test_gloss_text_aligns_tokens(self):
        g = self.a.gloss_text('Niquitta in calli.')
        self.assertEqual([t['token'] for t in g], ['Niquitta', 'in', 'calli'])
        self.assertEqual(g[1]['best']['class_'], 'particle')


class ConcordanceAndHintsTests(unittest.TestCase):
    rows = [dict(id='p1', iso='nci', nah='Niquitta in calli', es='Veo la casa', document='A'),
            dict(id='p2', iso='nci', nah='In nocal', es='Mi casa', document='A'),
            dict(id='p3', iso='nci', nah='Calco nemi', es='Vive en la casa', document='B'),
            dict(id='p4', iso='nci', nah='in xochitl', es='la flor', document='B'),
            dict(id='p5', iso='nhw', nah='kali', es='casa', document='C')]

    def test_stem_concordance_finds_inflected_forms(self):
        a = Analyzer(lexicon_records())
        c = StemConcordance(a, self.rows)
        hit = c.lookup('calli')
        self.assertEqual(hit['stem'], 'kal')
        self.assertEqual({p['id'] for p in c.lookup('calli', limit=10)['passages']}, {'p1', 'p2', 'p3'})
        self.assertNotIn('p5', {p['id'] for p in hit['passages']})  # solo náhuatl clásico
        self.assertNotIn('p2', {p['id'] for p in c.lookup('calli', exclude='p2')['passages']})

    def test_ibm1_hints_carry_supporting_passages(self):
        a = Analyzer(lexicon_records())
        h = GlossHints.train(a, self.rows, min_count=2)
        top = h.hints('kal', min_support=2)
        self.assertEqual(top[0]['es'], 'casa')
        self.assertTrue(set(top[0]['passages']) <= {'p1', 'p2', 'p3'})
        again = GlossHints.from_json(json.loads(json.dumps(h.to_json())))
        self.assertEqual(again.hints('kal', min_support=2), top)

    def test_spanish_tokens_drop_stopwords(self):
        self.assertEqual([k for k, _ in es_tokens('Veo la casa y las flores')], ['veo', 'casa', 'flor'])


class WordStudyServiceTests(unittest.TestCase):
    def test_word_and_gloss_validate_input(self):
        ws = WordStudy(root=ROOT)
        ws._ready = (Analyzer(lexicon_records()), StemConcordance(Analyzer(lexicon_records()), ConcordanceAndHintsTests.rows),
                     GlossHints({}, {}, {}, dict(version='test')))
        r = ws.word('nocal')
        self.assertEqual(r['analyses'][0]['segmentation'], 'no-cal')
        self.assertEqual(r['method']['model_calls'], 0)
        for bad in ('', 'dos palabras', 'x' * 61, '<script>'):
            with self.assertRaises(ValueError):
                ws.word(bad)
        g = ws.gloss('Niquitta in calli')
        self.assertEqual([t['segmentation'] for t in g['tokens']], ['Ni-qu-itta', 'in', 'cal-li'])
        self.assertEqual(g['tokens'][0]['gloss_source'], 'dictionary')
        with self.assertRaises(ValueError):
            ws.gloss('x' * 1201)

    def test_platform_endpoints(self):
        from nahuatl_local.corpus import CorpusStore
        from nahuatl_local.platform import make_server
        ws = WordStudy(root=ROOT)
        ws._ready = (Analyzer(lexicon_records()), StemConcordance(Analyzer(lexicon_records()), ConcordanceAndHintsTests.rows),
                     GlossHints({}, {}, {}, dict(version='test')))
        with tempfile.TemporaryDirectory() as d:
            store = CorpusStore(Path(d) / 'voces.sqlite3')
            import nahuatl_local.platform as platform
            original = platform.WordStudy
            platform.WordStudy = lambda **kw: ws
            try:
                httpd = make_server(store, port=0)
            finally:
                platform.WordStudy = original
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            try:
                base = f'http://127.0.0.1:{httpd.server_address[1]}'
                r = json.load(urllib.request.urlopen(base + '/api/word?w=niquitta'))
                self.assertEqual(r['analyses'][0]['segmentation'], 'ni-qu-itta')
                g = json.load(urllib.request.urlopen(base + '/api/gloss?id=axolotl-05338'))
                self.assertEqual(g['archive_id'], 'axolotl-05338')
                self.assertEqual(g['tokens'][0]['segmentation'], 'NI-QU-ITTA')
                with self.assertRaises(urllib.error.HTTPError) as err:
                    urllib.request.urlopen(base + '/api/word?w=dos%20palabras')
                self.assertEqual(err.exception.code, 400)
                js = urllib.request.urlopen(base + '/morphology.js').read().decode()
                self.assertIn('bindWordStudy', js)
            finally:
                httpd.shutdown(); httpd.server_close()


class GoldSetTests(unittest.TestCase):
    def test_gold_set_is_well_formed(self):
        gold = json.loads((ROOT / 'evaluation' / 'morphology-gold-v1.json').read_text(encoding='utf-8'))
        words = [i['word'] for i in gold['items']]
        self.assertEqual(len(words), len(set(words)))
        for item in gold['items']:
            self.assertIn(item['split'], ('dev', 'test'))
            self.assertEqual(item['segmentation'].replace('-', '').casefold(), item['word'].casefold())


if __name__ == '__main__':
    unittest.main()
