"""Sync completed local-model summaries to a separate public data file."""
import hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
ROOT=Path(__file__).resolve().parent
LOCAL_DB=Path(r'D:\AI-Industry-Radar\TrendRadar\output\ai_summaries.db')
TARGET=ROOT/'data/local_summaries.json'
def git(*args):
 r=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True,timeout=60)
 if r.returncode:raise RuntimeError((r.stderr or r.stdout).strip()[:500])
 return r.stdout.strip()
def local_key(url):
 u=urlsplit(url);return hashlib.sha256(urlunsplit((u.scheme,u.netloc,u.path,'','')).encode()).hexdigest()
def main():
 if not LOCAL_DB.exists():print('本地摘要数据库不存在');return
 # Do not modify the checkout while source changes are uncommitted.
 if git('status','--porcelain','--untracked-files=no'):print('仓库有未提交的更改，跳过同步');return
 git('pull','--rebase','origin','main')
 news=json.loads((ROOT/'data/news.json').read_text(encoding='utf-8'))
 cloud=json.loads((ROOT/'data/summaries.json').read_text(encoding='utf-8')).get('items',{}) if (ROOT/'data/summaries.json').exists() else {}
 with sqlite3.connect(f'file:{LOCAL_DB.as_posix()}?mode=ro',uri=True,timeout=15) as c:
  rows={r[0]:r[1:] for r in c.execute("select key,title_zh,summary,basis,saved_at from summaries where summary != ''")}
 summaries={}
 for item in news['items']:
  key=local_key(item['url']); row=rows.get(key)
  if not row or cloud.get(item['id'],{}).get('summary'):continue
  title,summary,basis,saved=row
  summaries[item['id']]={'title_zh':title,'summary':[x.strip() for x in summary.splitlines() if x.strip()],'company':[],'topics':[],'basis':'本地模型：'+(basis or '原文'),'summarized_at':saved}
 temp=TARGET.with_suffix('.tmp');temp.write_text(json.dumps({'items':summaries},ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(TARGET)
 git('add','data/local_summaries.json')
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0:print('没有新增的本地摘要');return
 git('-c','user.name=AI Radar','-c','user.email=ai-radar@localhost','commit','-m','Sync local summaries')
 for attempt in range(3):
  try:git('pull','--rebase','origin','main');git('push','origin','HEAD:main');print('本地摘要同步完成:',len(summaries));return
  except RuntimeError:
   if attempt==2:raise
if __name__=='__main__':
 try:main()
 except (OSError,RuntimeError,sqlite3.Error,subprocess.TimeoutExpired) as e:print('本地摘要同步暂未完成:',str(e)[:300]);sys.exit(1)
