import unittest,socket
from unittest.mock import patch
from nahuatl_local.review import request_bundle,local_review,validate_request
class ReviewTests(unittest.TestCase):
    def test_no_fake_probabilities_or_acceptance(self):
        r=local_review({'input':'hola','text':'inventado','related_passages':[]})
        self.assertIsNone(r['semantic_fidelity']);self.assertFalse(r['automatic_acceptance'])
    def test_exact_pair_not_certified(self):
        row={'id':'test','es':'entrada','nah':'salida'}
        r=local_review({'input':'entrada','text':'salida','related_passages':[row]})
        self.assertEqual(r['exact_aligned_pair_ids'],['test']);self.assertFalse(r['automatic_acceptance'])
    def test_export_offline(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('Network forbidden')):
            bundle=validate_request(request_bundle({'input':'entrada','text':'salida'}));self.assertEqual(bundle['schema_version'],1);self.assertIsNone(bundle['human_review']['fidelity']);self.assertNotIn('model',bundle)
if __name__=='__main__':unittest.main()
