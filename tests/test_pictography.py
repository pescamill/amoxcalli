import copy
import json
from pathlib import Path
import tempfile
import unittest

from nahuatl_local.pictography import load_catalog, public_catalog, validate, ROOT
from nahuatl_local.pictography_pipeline import parse_page, publish, write_new


class PictographyTests(unittest.TestCase):
    def setUp(self): self.catalog = load_catalog()

    def test_documentary_analysis_and_exact_values_are_separate(self):
        data = self.catalog
        summary = public_catalog({})['summary']
        self.assertEqual(len(data['occurrences']), summary['glyphs']+summary['personages'])
        self.assertEqual(sum(len(o['components']) for o in data['occurrences']), summary['components'])
        by_id = {o['id']:o for o in data['occurrences']}
        o = by_id['calpan:073_08_A_01']
        self.assertEqual(o['reading'], 'tecpan')
        self.assertEqual(o['components'], [{'element_id':'calpan:element:05.01.01','values':['tecpan']}])
        mh = by_id['mh-tianquiztenco:387_709v_01']
        self.assertEqual(mh['reading'], 'ichan tonalco *')
        self.assertEqual(mh['components'][0]['values'], ['chan'])
        self.assertTrue(mh['unexpressed'])
        self.assertFalse(data['rights']['training'])

    def test_public_links_require_a_public_sense(self):
        data = public_catalog({})
        self.assertTrue(all(not e['lexical_links'] for e in data['elements']))
        data = public_catalog({'sense-calli':{'kind':'sense'}})
        expected = sum(sum(link['sense_id'] == 'sense-calli' for link in e.get('lexical_links', []))
                       for e in self.catalog['elements'])
        self.assertEqual(sum(len(e['lexical_links']) for e in data['elements']), expected)
        self.assertGreater(expected, 0)
        self.assertNotIn('profile', data)
        self.assertNotIn('study', data)

    def test_rejects_cross_document_components_and_untrusted_images(self):
        data = copy.deepcopy(self.catalog)
        data['occurrences'][0]['components'][0]['element_id'] = 'telleriano:element:05.01.01'
        with self.assertRaises(ValueError): validate(data)
        data = copy.deepcopy(self.catalog)
        data['elements'][0]['image'] = 'https://example.org/image.png'
        with self.assertRaises(ValueError): validate(data)
        data = copy.deepcopy(self.catalog); data['rights']['training'] = True
        with self.assertRaises(ValueError): validate(data)

    def test_parser_ignores_embedded_lexical_data_and_keeps_uncertainty(self):
        raw = b'''<article class="lamina"><h3>L\xc3\xa1mina - P1</h3></article>
        <article class="zona"><h3>Zona - P1_A</h3>
        <article class="glifo"><h3>Glifo - P1_A_01</h3><p>Lectura: nombre ? *</p>
        <p>Cita: glosa original</p><article class="gdn"><p>Lectura: NO IMPORTAR</p></article>
        <article class="elemento"><h4>Elemento: calli</h4><p>Sentido: casa</p>
        <p>Valor fon\xc3\xa9tico: chan</p><p>https://tlachia.iib.unam.mx/elemento/05.01.01</p>
        <article class="gdn"><p>Sentido: NO IMPORTAR</p></article></article></article></article>'''
        parsed = parse_page(raw, {'locator':'P1','url':'https://tlachia.iib.unam.mx/calpan/P1'}, {'id':'calpan'}, [])
        self.assertEqual(parsed['occurrences'][0]['reading'], 'nombre ? *')
        self.assertEqual(parsed['occurrences'][0]['citations'], ['glosa original'])
        self.assertEqual(parsed['elements'][0]['meanings'], ['casa'])
        self.assertEqual(parsed['occurrences'][0]['components'][0]['values'], ['chan'])
        with self.assertRaises(ValueError):
            parse_page(b'<html>Formato nuevo</html>', {'locator':'P1','url':'https://tlachia.iib.unam.mx/calpan/P1'}, {'id':'calpan'}, [])

    def test_missing_reading_is_deferred_instead_of_guessed(self):
        raw = b'''<article class="lamina"><h3>L\xc3\xa1mina - P1</h3></article>
        <article class="glifo"><h3>Glifo - P1_01</h3></article>
        <article class="glifo"><h3>Glifo - P1_02</h3><p>Lectura: ?</p></article>'''
        parsed = parse_page(raw, {'locator':'P1','url':'https://tlachia.iib.unam.mx/calpan/P1'}, {'id':'calpan'}, [])
        self.assertEqual(len(parsed['occurrences']), 1)
        self.assertEqual(parsed['exceptions'][0]['code'], 'P1_01')

    def test_additive_publication_preserves_edits_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'catalog.json'
            self.assertEqual(publish(self.catalog, path), 'created')
            self.assertEqual(publish(self.catalog, path), 'unchanged')
            edited = copy.deepcopy(self.catalog); edited['occurrences'][0]['reading'] = 'EDICION LOCAL'
            path.write_text(json.dumps(edited))
            before = path.read_bytes()
            with self.assertRaises(ValueError): publish(self.catalog, path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(write_new(Path(directory)/'candidate.json', self.catalog), 'created')
            self.assertEqual(write_new(Path(directory)/'candidate.json', self.catalog), 'unchanged')
            with self.assertRaises(ValueError): write_new(Path(directory)/'candidate.json', edited)

    def test_adds_a_distinct_batch_with_public_backup(self):
        candidate = copy.deepcopy(self.catalog)
        candidate['release_id'] = 'second-batch'
        extra = copy.deepcopy(candidate['occurrences'][0]); extra['id'] += '-new'; extra['code'] += '-new'
        candidate['occurrences'].append(extra)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'catalog.json'; publish(self.catalog, path)
            self.assertEqual(publish(candidate, path), 'added')
            result = load_catalog(path)
            self.assertEqual(result['occurrences'][:-1], self.catalog['occurrences'])
            self.assertEqual(load_catalog(Path(directory)/'catalog-before-second-batch.json'), self.catalog)

    def page_extension(self, old):
        document = old['documents'][0]
        page = copy.deepcopy(old['pages'][0])
        page.update(id=document['id']+':synthetic-P2', locator='synthetic-P2',
                    url='https://tlachia.iib.unam.mx/'+document['id']+'/synthetic-P2')
        element = copy.deepcopy(next(e for e in old['elements'] if e['document_id'] == document['id']))
        element['url'] = page['url']
        occurrence = copy.deepcopy(next(o for o in old['occurrences'] if o['page_id'] == old['pages'][0]['id']))
        occurrence.update(id=document['id']+':synthetic-P2_01', code='synthetic-P2_01',
                          page_id=page['id'], zone_id=None, url=page['url'],
                          components=[dict(element_id=element['id'], values=['synthetic-test-only'])])
        return dict(schema_version=1, release_id='synthetic-second-page',
                    attribution=old['attribution'], rights=copy.deepcopy(old['rights']),
                    documents=[copy.deepcopy(document)], pages=[page], zones=[],
                    elements=[element], occurrences=[occurrence])

    def test_reuses_element_on_another_page_without_touching_original_fields(self):
        old = copy.deepcopy(self.catalog)
        old['elements'][0]['notes'] = ['Preserve this local editorial note.']
        candidate = self.page_extension(old)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'catalog.json'
            publish(old, path)
            before = path.read_bytes()
            self.assertEqual(publish(candidate, path), 'added')
            result = load_catalog(path)
            for key in ('documents', 'pages', 'zones', 'elements', 'occurrences'):
                self.assertEqual(result[key][:len(old[key])], old[key])
            self.assertEqual(len(result['elements']), len(old['elements']))
            self.assertEqual(result['elements'][0]['url'], old['elements'][0]['url'])
            self.assertEqual(result['elements'][0]['notes'], old['elements'][0]['notes'])
            backup = path.with_name('catalog-before-synthetic-second-page.json')
            self.assertEqual(backup.read_bytes(), before)
            published = path.read_bytes()
            self.assertEqual(publish(candidate, path), 'unchanged')
            self.assertEqual(path.read_bytes(), published)

    def test_same_element_with_changed_semantics_or_notes_is_rejected(self):
        old = copy.deepcopy(self.catalog)
        old['elements'][0]['notes'] = ['Original note']
        changes = dict(designation='Changed designation', meanings=['Changed meaning'],
                       image='https://tlachia.iib.unam.mx/archivos/calpan/imagenes/changed.jpg',
                       lexical_links=[dict(sense_id='sense-calli', relation='designation', note='Changed scope')],
                       notes=['Changed note'], extra_field='Unapproved addition')
        for field, value in changes.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'catalog.json'
                publish(old, path)
                before = path.read_bytes()
                candidate = self.page_extension(old)
                candidate['elements'][0][field] = value
                with self.assertRaises(ValueError):
                    publish(candidate, path)
                self.assertEqual(path.read_bytes(), before)
                self.assertFalse(path.with_name('catalog-before-synthetic-second-page.json').exists())


if __name__ == '__main__': unittest.main()
