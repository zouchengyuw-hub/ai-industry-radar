import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import radar
class RadarTests(unittest.TestCase):
 def test_url(self):
  self.assertEqual(radar.clean_url('https://example.com/a?x=1&utm_source=z#z'),'https://example.com/a?x=1')
  self.assertIsNone(radar.clean_url('javascript:alert(1)'))
 def test_collect_preserves_first_seen_and_deduplicates(self):
  with tempfile.TemporaryDirectory() as d, patch.object(radar,'NEWS',Path(d)/'news.json'):
   item={'id':'123','title':'x','url':'https://example.com/x','source':'test','source_id':'t','priority':0,'published':None}
   with patch.object(radar,'get_feed',return_value=('t',[item],None)):
    radar.collect([{'id':'t'}]);first=radar.load(radar.NEWS,{})['items'][0]['first_seen'];radar.collect([{'id':'t'}]);data=radar.load(radar.NEWS,{})
   self.assertEqual(len(data['items']),1);self.assertEqual(data['items'][0]['first_seen'],first)
 def test_ai_off_by_default(self):
  with tempfile.TemporaryDirectory() as d,patch.object(radar,'NEWS',Path(d)/'news.json'),patch.object(radar,'SUMMARIES',Path(d)/'summaries.json'),patch.dict('os.environ',{},clear=True):
   radar.summarize();self.assertFalse(radar.SUMMARIES.exists())
if __name__=='__main__':unittest.main()
