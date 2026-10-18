import unittest
from experiments.llm.runtime import encode_pair
class FakeTokenizer:
    eos_token_id=9
    def apply_chat_template(self,*args,**kwargs):return [1,2,3]
    def __call__(self,*args,**kwargs):return {'input_ids':[4,5]}
class RuntimeTests(unittest.TestCase):
    def test_label_mask_and_no_truncation(self):
        row={'es':'casa bonita','nah':'test target'}
        encoded=encode_pair(FakeTokenizer(),row,6)
        self.assertEqual(encoded['labels'],[-100,-100,-100,4,5,9])
        self.assertIsNone(encode_pair(FakeTokenizer(),row,5))


if __name__=='__main__':unittest.main()
