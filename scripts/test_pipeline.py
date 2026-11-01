import copy,json,unittest
from common import ROOT,asset,alignment_words
from project import validate
class Pipeline(unittest.TestCase):
 def setUp(self):
  self.p=json.loads((ROOT/'examples/one-clear-idea/project.json').read_text())
  for d in self.p['dialogue']:d.pop('audio',None)
 def test_sample(self):self.assertEqual(validate(self.p),[])
 def test_gap_rejected(self):
  self.p['shots'][1]['start']+=.5;self.assertTrue(validate(self.p))
 def test_invalid_layout(self):
  self.p['shots'][0]['layout']='missing';self.assertTrue(validate(self.p))
 def test_nan_rejected(self):
  self.p['shots'][0]['end']=float('nan');self.assertTrue(validate(self.p))
 def test_outside_audio(self):
  with self.assertRaises(ValueError):asset('../../../.env')
 def test_overlap_rejected(self):
  self.p['dialogue'][1]['start']=1;self.assertTrue(validate(self.p))
 def test_template_count(self):
  self.p['shots'][0]['items']=['one'];self.assertTrue(validate(self.p))
 def test_word_offsets(self):
  words=alignment_words({'characters':list('Hi all'),'character_start_times_seconds':[0,.1,.2,.3,.4,.5],'character_end_times_seconds':[.1,.2,.3,.4,.5,.6]},6)
  self.assertEqual(words,[{'text':'Hi','start':6,'end':6.2},{'text':'all','start':6.3,'end':6.6}])
if __name__=='__main__':unittest.main()
