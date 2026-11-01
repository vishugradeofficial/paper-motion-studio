from pathlib import Path
import hashlib,json,os,subprocess,urllib.request
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SR=48000
def load_project(path):
    p=Path(path).resolve();return p,json.loads(p.read_text())
def asset(name):
    p=(ROOT/'studio/public'/name).resolve()
    if not p.is_relative_to((ROOT/'studio/public').resolve()):raise ValueError('Audio path must stay inside studio/public')
    return p
def key():
    value=os.environ.get('ELEVENLABS_API_KEY')
    if value:return value
    p=ROOT/'.env'
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip().startswith('ELEVENLABS_API_KEY='):return line.split('=',1)[1].strip().strip('"\'')
    raise ValueError('Set ELEVENLABS_API_KEY in environment or .env; do not put it in a project file.')
def request(endpoint,body):
    req=urllib.request.Request('https://api.elevenlabs.io'+endpoint,data=json.dumps(body).encode(),headers={'xi-api-key':key(),'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=240) as response:
        cost=response.headers.get('character-cost')
        return response.read(),int(cost) if cost and cost.isdigit() else None
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()[:18]
def decode(path):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar',str(SR),'-f','f32le','-']);return np.frombuffer(raw,np.float32).copy()
def wav(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ac','1','-ar',str(SR),'-i','-','-c:a','pcm_f32le',str(path)],input=np.asarray(x,np.float32).tobytes(),check=True)
def loudness(path):
    import re
    r=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    data=json.loads(re.findall(r'\{[\s\S]*?\}',r.stderr)[-1]);return float(data['input_i']),float(data['input_tp'])

def alignment_words(alignment,offset=0):
    import re
    chars=alignment.get('characters',[]);starts=alignment.get('character_start_times_seconds',[]);ends=alignment.get('character_end_times_seconds',[])
    if not(len(chars)==len(starts)==len(ends)):raise ValueError('Invalid character alignment')
    return [{'text':m.group(),'start':round(offset+starts[m.start()],4),'end':round(offset+ends[m.end()-1],4)} for m in re.finditer(r'\S+',''.join(chars))]
