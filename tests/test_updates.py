"""Aviso de versión nueva: comparación, caché diaria y silencio sin red."""
import json
import tempfile
import unittest
from pathlib import Path

from nahuatl_local.updates import DAY, Updates, parse


class UpdatesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name) / 'derived/update-check.json'
        self.calls = 0

    def tearDown(self):
        self.temp.cleanup()

    def updates(self, tag='v0.1.3', current='0.1.2', fail=False, git=False):
        def fetch():
            self.calls += 1
            if fail:
                raise OSError('sin red')
            return dict(tag=tag, notes='Novedades')
        return Updates(current, self.cache, fetch, git)

    def test_parse(self):
        self.assertEqual(parse('v0.1.10'), (0, 1, 10))
        self.assertGreater(parse('v0.1.10'), parse('0.1.9'))
        for bad in ('', None, 'latest', 'v1.2'):
            self.assertIsNone(parse(bad))

    def test_newer_release_is_announced_with_how_to_update(self):
        s = self.updates().check(now=1000)
        self.assertEqual((s['available'], s['latest'], s['how']), (True, '0.1.3', 'zip'))
        self.assertTrue(s['url'].startswith('https://github.com/pescamill/amoxcalli/releases'))
        self.assertEqual(self.updates(git=True).check(now=1000)['how'], 'git')

    def test_same_or_older_release_is_quiet(self):
        for tag in ('v0.1.2', 'v0.1.1', 'nonsense'):
            self.cache.unlink(missing_ok=True)
            self.assertEqual(self.updates(tag).check(now=1000), dict(current='0.1.2', available=False))

    def test_checks_github_at_most_once_a_day(self):
        self.updates().check(now=1000)
        self.updates().check(now=1000 + DAY - 1)
        self.assertEqual(self.calls, 1)
        self.updates().check(now=1000 + DAY + 1)
        self.assertEqual(self.calls, 2)

    def test_offline_is_silent_and_keeps_last_answer(self):
        self.assertFalse(self.updates(fail=True).check(now=1000)['available'])
        self.updates().check(now=1000)
        self.assertTrue(self.updates(fail=True).check(now=1000 + 2 * DAY)['available'])
        self.assertEqual(json.loads(self.cache.read_text())['tag'], 'v0.1.3')


if __name__ == '__main__':
    unittest.main()
