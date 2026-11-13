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
class SummaryTests(unittest.TestCase):
 def test_persists_summary_and_quota(self):
  with tempfile.TemporaryDirectory() as d, patch.object(radar,'NEWS',Path(d)/'news.json'), patch.object(radar,'SUMMARIES',Path(d)/'summaries.json'), patch.dict('os.environ',{'ENABLE_FREE_AI':'true','GEMINI_API_KEY':'test-key','AI_DAILY_LIMIT':'1'},clear=True):
   radar.save(radar.NEWS,{'items':[{'id':'a','title':'A','url':'https://example.com','priority':0,'first_seen':'2026-11-13T00:00:00Z','published':None}]})
   with patch.object(radar,'fetch_article',return_value=('a'*400,None)),patch.object(radar,'gemini_batch',return_value={'a':{'title_zh':'标题','summary':['要点']}}):radar.summarize()
   result=radar.load(radar.SUMMARIES,{})
   self.assertEqual(result['items']['a']['summary'],['要点']);self.assertEqual(sum(result['quota'].values()),1)
 def test_inaccessible_article_does_not_count_as_model_call(self):
  with tempfile.TemporaryDirectory() as d, patch.object(radar,'NEWS',Path(d)/'news.json'), patch.object(radar,'SUMMARIES',Path(d)/'summaries.json'), patch.dict('os.environ',{'ENABLE_FREE_AI':'true','GEMINI_API_KEY':'test-key'},clear=True):
   radar.save(radar.NEWS,{'items':[{'id':'a','title':'A','url':'https://example.com','priority':0,'first_seen':'2026-11-13T00:00:00Z','published':None}]})
   with patch.object(radar,'fetch_article',return_value=(None,'正文不可用')),patch.object(radar,'gemini_batch') as model:radar.summarize()
   result=radar.load(radar.SUMMARIES,{});self.assertEqual(result['items']['a']['error'],'正文不可用');model.assert_not_called()
class BatchTests(unittest.TestCase):
 def test_batch_ignores_unknown_ids_and_tracks_missing_items(self):
  fake_response={'candidates':[{'content':{'parts':[{'text':json.dumps({'articles':[{'id':'a','title':'标题','summary':['要点']},{'id':'unknown','title':'无关','summary':['无关']}]},ensure_ascii=False)}]}}]}
  from unittest.mock import Mock
  response=Mock(status_code=200,ok=True);response.json.return_value=fake_response
  with patch.object(radar.SESSION,'post',return_value=response):
   out=radar.gemini_batch([({'id':'a','title':'A'},'正文'),({'id':'b','title':'B'},'正文')],'test-key','model')
  self.assertEqual(set(out),{'a'});self.assertEqual(out['a']['summary'],['要点'])
 def test_transient_failure_retries_within_15_minutes(self):
  import datetime
  with tempfile.TemporaryDirectory() as d, patch.object(radar,'NEWS',Path(d)/'news.json'), patch.object(radar,'SUMMARIES',Path(d)/'summaries.json'), patch.dict('os.environ',{'ENABLE_FREE_AI':'true','GEMINI_API_KEY':'test-key'},clear=True):
   radar.save(radar.NEWS,{'items':[{'id':'a','title':'A','url':'https://example.com','priority':0,'first_seen':'2026-11-13T00:00:00Z','published':None}]})
   with patch.object(radar,'fetch_article',return_value=('x'*500,None)),patch.object(radar,'gemini_batch',side_effect=ValueError('模型 API HTTP 503')):radar.summarize()
   item=radar.load(radar.SUMMARIES,{})['items']['a'];retry=datetime.datetime.fromisoformat(item['retry_after'].replace('Z','+00:00'))
   self.assertLessEqual((retry-radar.now()).total_seconds(),900);self.assertIn('503',item['error'])
if __name__=='__main__':unittest.main()
