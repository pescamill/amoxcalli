import tempfile
import unittest
from pathlib import Path
from nahuatl_local.corpus import CorpusStore
from experiments.llm.compose import rule_query


class RuleQueryTests(unittest.TestCase):
    def test_rules_ported_without_faking_general_translation(self):
        with tempfile.TemporaryDirectory() as d:
            store=CorpusStore(Path(d)/'rules.sqlite3')
            self.assertEqual(rule_query(store,'Veo una flor.')['status'],'proposal')
            self.assertEqual(rule_query(store,'El sol y la luna')['status'],'proposal')
            self.assertEqual(rule_query(store,'No veo tres casas mañana')['status'],'insufficient')


if __name__=='__main__':unittest.main()
