#!/usr/bin/env python3
"""Suite por archivos: dos procesos independientes,180 s máximos por proceso."""
import argparse
import concurrent.futures
import json
import os
import re
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--resume',action='store_true');p.add_argument('--max-files',type=int,default=0)
    a=p.parse_args()
    if a.max_files<0:p.error('--max-files debe ser no negativo')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=a.resume)
    files=sorted((ROOT/'tests').glob('test_*.py'));completed=[];pending=[]
    old={r['file']:r for r in json.loads((out/'results.json').read_text()).get('results',[])} if (out/'results.json').exists() else {}
    for path in files:
        log=out/(path.stem+'.txt');text=log.read_text() if log.exists() else ''
        match=re.search(r'Ran (\d+) tests? in ([0-9.]+)s',text)
        if a.resume and match and text.rstrip().endswith('OK'):
            row=old.get(str(path.relative_to(ROOT)),{'file':str(path.relative_to(ROOT)),'exit_code':0,
                    'duration_seconds':float(match[2]),'log':str(log.relative_to(ROOT)) if log.is_relative_to(ROOT) else str(log)})
            completed.append(row)
        else:pending.append(path)
    selected=pending[:a.max_files] if a.max_files else pending
    def save(rows):
        (out/'results.json').write_text(json.dumps({'passed':len(rows)==len(files) and all(r['exit_code']==0 for r in rows),
              'completed':len(rows),'total_files':len(files),'results':sorted(rows,key=lambda r:r['file'])},indent=2)+'\n')
    def run(path):
        started=time.monotonic();log=out/(path.stem+'.txt')
        try:
            with log.open('w') as stream:
                result=subprocess.run(['python3','-m','unittest','discover','-s','tests','-p',path.name],
                                      cwd=ROOT,env=dict(os.environ,PYTHONPATH='src'),stdout=stream,stderr=subprocess.STDOUT,timeout=180)
            code=result.returncode
        except subprocess.TimeoutExpired:code=124
        return {'file':str(path.relative_to(ROOT)),'exit_code':code,'duration_seconds':round(time.monotonic()-started,3),
                'log':str(log.relative_to(ROOT)) if log.is_relative_to(ROOT) else str(log)}
    rows=list(completed);save(rows)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(run,selected):
            rows.append(row)
            save(rows)
            print(row['file'],row['exit_code'],flush=True)
    return 0 if all(r['exit_code']==0 for r in rows) else 1

if __name__=='__main__':raise SystemExit(main())
