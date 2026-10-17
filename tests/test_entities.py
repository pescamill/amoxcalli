import json
import unittest

from nahuatl_local import entities
from nahuatl_local.entities import Entities, day_index, trecena_of


class EntitiesData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = Entities()
        cls.data = cls.service.data()
        cls.seed = json.loads(entities.SEED.read_text())

    def test_counts_and_provenance(self):
        deities = [e for e in self.data['entities'] if e['kind'] == 'deity']
        self.assertGreaterEqual(len(deities), 12)
        for e in self.data['entities']:
            self.assertTrue(e['attributes'] or e['senses'], e['id'])
            for a in e['attributes'] + e['relations'] + e['epithets']:
                self.assertTrue(a['sources'], e['id'])
                for s in a['sources']:
                    self.assertTrue(s.get('license'), (e['id'], s))
        cal = self.data['calendar']
        self.assertEqual([s['n'] for s in cal['signs']], list(range(1, 21)))
        self.assertEqual([n['n'] for n in cal['numerals']], list(range(1, 14)))
        self.assertEqual(len(cal['trecenas']), 20)
        for s in cal['signs']:
            self.assertTrue(s['gloss_sources'], s['name'])
            self.assertTrue(s['glyphs'], s['name'])  # cada signo tiene un glifo documentado en Tlachia
        veintenas = [v for v in cal['veintenas'] if v['kind'] == 'veintena']
        self.assertEqual(len(veintenas), 18)
        for v in cal['veintenas']:
            self.assertTrue(v['position']['sources'], v['name'])
        self.assertEqual([v['name'] for v in cal['veintenas'] if v['name_pending']], ['teotleco', 'nemontemi'])

    def test_variant_spellings_lead_to_the_same_card(self):
        for query, eid in [('Huitzilopochtli', 'huitzilopochtli'), ('Uitzilopochtli', 'huitzilopochtli'),
                           ('Huitzillopochtli', 'huitzilopochtli'), ('Huitzilopuchtli', 'huitzilopochtli'),
                           ('Vitzilopochtli', 'huitzilopochtli'), ('Quetzalcohuatl', 'quetzalcoatl'), ('Quetzalcóatl', 'quetzalcoatl'),
                           ('Tezcatlipuca', 'tezcatlipoca'), ('Tlalloc', 'tlaloc'), ('Xippe', 'xipe-totec'), ('Tlazolteutl', 'tlazolteotl'),
                           ('Mictlanteuctli', 'mictlantecuhtli'), ('Tloque Nauaque', 'tloque-nahuaque'), ('Ipalnemoani', 'ipalnemohuani'),
                           ('yzcalli', 'veintena-izcalli'), ('hueytoçoztli', 'veintena-hueytozoztli'), ('cohuatl', 'signo-coatl')]:
            matches = self.service.search(query)['matches']
            self.assertTrue(matches, query)
            self.assertEqual(matches[0]['id'], eid, query)

    def test_homographs_and_dates(self):
        self.assertEqual(self.service.search('itztli')['matches'], [])  # obsidiana, no el Señor de la Noche
        self.assertEqual(self.service.search('Ce Acatl')['matches'][-1]['id'], 'dia/1-12')
        self.assertEqual(self.service.search('chiuhcnahui tecpatl')['matches'][0]['id'], 'dia/9-17')

    def test_calendar_arithmetic(self):
        self.assertEqual(trecena_of(1, 0), 1)
        self.assertEqual(trecena_of(6, 19), 19)  # 6 Xochitl, lámina 26r: trecena 1 Cuauhtli
        self.assertEqual(day_index(1, 0), 0)
        self.assertEqual(day_index(13, 19), 259)
        self.assertEqual(self.data['calendar']['trecenas'][18]['name'], 'ce cuauhtli')
        self.assertIn('xochiquetzal', self.data['calendar']['trecenas'][18]['figures'])
        self.assertGreaterEqual(self.data['calendar']['check']['pages_with_days'], 10)

    def test_no_restricted_sources_shown(self):
        restricted = set(self.seed['restricted_documents'])
        rows = self.service.rows()
        for e in self.data['entities']:
            for p in e['passages']['sample']:
                self.assertNotIn(rows[p['id']]['document'], restricted)
                self.assertNotIn(p['id'], self.seed['restricted_passages'])
        recipe = json.loads(entities.RECIPE.read_text())
        ids = [x['archive_id'] for l in recipe['lessons'] for x in l['examples']]
        self.assertTrue(all(rows[i]['document'] not in restricted for i in ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_wiktionary_revisions_are_pinned(self):
        for e in self.data['entities']:
            for a in e['attributes']:
                for s in a['sources']:
                    if s['kind'] == 'wiktionary':
                        self.assertIn('oldid=', s['url'])

    def test_readings_and_unit_are_drafts_in_the_queue(self):
        catalog = self.service.catalog()
        self.assertGreaterEqual(len(catalog['readings']), 3)
        self.assertTrue(all(r['review']['status'] == 'automatic_draft' for r in catalog['readings']))
        self.assertEqual(catalog['unit']['review']['status'], 'automatic_draft')
        self.assertEqual(catalog['review']['status'], 'automatic_draft')
        queue = json.loads(entities.QUEUE.read_text())
        tasks = {t['id'] for t in queue['tasks']}
        self.assertIn('unit-calendario-review', tasks)
        self.assertIn('entities-seed-review', tasks)
        self.assertTrue({f'myth-reading-{r["id"]}-review' for r in catalog['readings']} <= tasks)
        proposal = json.loads(entities.PROPOSAL.read_text())
        self.assertFalse(proposal['summary']['linguistic_certification'])
        unit = self.service.unit()['units'][0]
        self.assertEqual({e['kind'] for e in unit['exercises']}, {'match', 'identify', 'build', 'cloze', 'translate'})
        self.assertTrue(set(unit['passages']) >= {unit['closing']['archive_id']})

    def test_card_hydrates_passages(self):
        card = self.service.get('huitzilopochtli')
        self.assertTrue(card['passages']['rows'])
        self.assertGreater(card['passages']['restricted'], 0)  # se cuentan, no se muestran
        day = self.service.day(1, 4)  # Ce Coatl
        self.assertTrue(day['rows'] or day['glyph_rows'])
        with self.assertRaises(KeyError):
            self.service.get('no-existe')


class EntitiesGeneration(unittest.TestCase):
    def test_generated_files_are_current(self):
        files, _ = entities.generate(write=False)
        stale = [str(p) for p, raw in files.items() if not p.exists() or p.read_bytes() != raw]
        self.assertEqual(stale, [], 'Ejecuta python3 -m nahuatl_local.entities')

    def test_unsourced_quote_is_rejected(self):
        from nahuatl_local.lexicon import load_records
        seed = json.loads(entities.SEED.read_text())
        ctx = entities.Context(load_records(), None, seed)
        with self.assertRaises(ValueError):
            ctx.source(dict(passage='axolotl-04318', quote='Quetzalcoatl'), 'prueba')
        with self.assertRaises(ValueError):
            ctx.source(dict(passage='axolotl-06333', quote='tonatiuh'), 'prueba')  # restringido


if __name__ == '__main__':
    unittest.main()
