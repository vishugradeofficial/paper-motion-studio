from pathlib import Path
import argparse,base64,json,re,subprocess,sys,urllib.error
import numpy as np
from common import ROOT,SR,asset,load_project,decode,wav,request,fingerprint,loudness

def generate(p,kind,paid,replace=False,line=None):
    folder=ROOT/'studio/public/generated'/p['slug'];folder.mkdir(parents=True,exist_ok=True);ledger=ROOT/'work'/p['slug']/'credits.json';ledger.parent.mkdir(parents=True,exist_ok=True)
    entries=json.loads(ledger.read_text()) if ledger.exists() else [];pending=[]
    items=p['dialogue'] if kind=='voice' else [e for e in p.get('sound',[]) if e.get('prompt')]
    for item in items:
        if line and item['id']!=line:continue
        existing=item.get('audio') if kind=='voice' else item.get('source')
        if existing and not replace and asset(existing).exists():continue
        if kind=='voice':
            voice=item.get('voiceId') or p.get('voiceId');model=item.get('model','eleven_v3')
            if not voice:raise ValueError('Choose a character voiceId before generation')
            body={'text':item['text'],'model_id':model};endpoint=f'/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128'
        else:
            body={'text':item['prompt'],'duration_seconds':item.get('generateDuration',min(10,item['end']-item['start'])),'prompt_influence':.3};endpoint='/v1/sound-generation'
        sig=fingerprint([endpoint,body]);target=folder/(kind+'-'+sig+'.mp3');meta=target.with_suffix('.json')
        pending.append({'id':item['id'],'characters':len(body['text']),'cache_hit':target.exists(),'kind':kind})
        if not paid:continue
        if not target.exists():
            raw,cost=request(endpoint,body)
            if kind=='voice':
                data=json.loads(raw);target.write_bytes(base64.b64decode(data['audio_base64']));meta.write_text(json.dumps({'request':body,'alignment':data.get('alignment'),'credits':cost},indent=2))
            else:target.write_bytes(raw);meta.write_text(json.dumps({'request':body,'credits':cost},indent=2))
            entries.append({'id':item['id'],'kind':kind,'fingerprint':sig,'credits':cost,'evidence':'API character-cost header' if cost is not None else 'Unknown: API did not return a credit charge'})
            ledger.write_text(json.dumps(entries,indent=2))
        rel=str(target.relative_to(ROOT/'studio/public'));item['audio' if kind=='voice' else 'source']=rel
    print(json.dumps({'mode':'generate' if paid else 'dry-run','requests':pending,'characters':sum(x['characters'] for x in pending),'note':'Character count is not a guaranteed credit quote. Cache hits and existing provided audio cost no new credits.'},indent=2))
    return p

def synth(name,duration,seed=19):
    n=round(duration*SR);t=np.arange(n)/SR;rng=np.random.default_rng(seed)
    if name=='rain':
        noise=rng.normal(0,1,n);return np.convolve(noise,np.ones(9)/9,mode='same').astype(np.float32)*.07
    if name=='clock':
        x=np.zeros(n)
        for k in range(0,n,SR):
            u=np.arange(min(round(.08*SR),n-k))/SR;x[k:k+len(u)]+=np.sin(u*2*np.pi*1800)*np.exp(-u*85)*.15
        return x
    if name=='click':return np.sin(t*2*np.pi*2300)*np.exp(-t*120)*.3
    if name=='bed':
        x=np.zeros(n)
        for k in range(0,n,SR*3):
            u=t[:min(SR*7,n-k)];x[k:k+len(u)]+=(np.sin(2*np.pi*196*u)+.5*np.sin(2*np.pi*246.94*u)+.25*np.sin(2*np.pi*293.66*u))*.025*np.exp(-u*.65)*(1-np.exp(-u*8))
        return x
    raise ValueError('Unknown procedural source '+name)

def loop_with_crossfade(x,n):
    """Overlap ambience tails instead of making a hard discontinuity every loop."""
    if len(x)>=n:return x[:n]
    overlap=min(round(.35*SR),len(x)//4)
    if overlap<2:return np.resize(x,n)
    source=np.asarray(x,dtype=np.float32).copy();source[:overlap]*=np.linspace(0,1,overlap);source[-overlap:]*=np.linspace(1,0,overlap)
    result=np.zeros(n,dtype=np.float32);step=len(source)-overlap
    for start in range(0,n,step):
        length=min(len(source),n-start);result[start:start+length]+=source[:length]
    return result

def mix(p):
    out=ROOT/'out'/p['slug'];out.mkdir(parents=True,exist_ok=True);generated=ROOT/'studio/public/generated'/p['slug'];generated.mkdir(parents=True,exist_ok=True)
    n=round(p['duration']*SR);voice=np.zeros(n,dtype=np.float32);foley=np.zeros(n,dtype=np.float32);music=np.zeros(n,dtype=np.float32);by_speaker={};cues=[]
    for d in p['dialogue']:
        if not d.get('audio'):continue
        x=decode(asset(d['audio']));a=round(d['start']*SR);slot=round((d['end']-d['start'])*SR)
        if len(x)>slot+round(.08*SR):raise ValueError('Speech does not fit '+d['id']+'; change timing or script')
        k=min(n-a,len(x));peak=float(np.max(np.abs(x))) if len(x) else 0
        if peak>0:x=x*min(2,.7/peak)
        voice[a:a+k]+=x[:k];speaker=d.get('speaker','miro');by_speaker.setdefault(speaker,np.zeros(n,dtype=np.float32));by_speaker[speaker][a:a+k]+=x[:k]
        cues.append({'id':d['id'],'start':d['start'],'end':d['start']+k/SR})
    for e in p.get('sound',[]):
        if not e.get('source'):continue
        a=round(e['start']*SR);b=round(e['end']*SR);source=e['source'];x=synth(source.split(':',1)[1],e['end']-e['start']) if source.startswith('procedural:') else decode(asset(source))
        if len(x)==0:raise ValueError('Empty sound '+e['id'])
        x=loop_with_crossfade(x,b-a) if e.get('loop',False) else np.pad(x[:b-a],(0,max(0,b-a-len(x))))
        fade=min(round(.04*SR),len(x)//3);x=x.copy();x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
        (music if e.get('role')=='music' else foley)[a:b]+=x*e.get('gain',1)
    # Smooth amplitude-derived ducking; do not claim RMS identifies spoken words.
    hop=round(SR*.02);activity=np.array([float(np.sqrt(np.mean(voice[k:k+hop]**2)))>.012 for k in range(0,n,hop)])
    envelope=np.convolve(activity.astype(float),np.ones(11)/11,mode='same');duck=1-.78*np.interp(np.arange(n),np.arange(len(envelope))*hop,envelope);music*=duck;foley*=1-.55*(1-duck)
    fade=min(SR,n//4);music[-fade:]*=np.linspace(1,0,fade);foley[-fade:]*=np.linspace(1,0,fade)
    mouth={}
    for speaker,x in by_speaker.items():
        mouth[speaker]=[round(min(1,max(0,(float(np.sqrt(np.mean(x[round(f*SR/p['fps']):round((f+1)*SR/p['fps'])]**2)))-.012)/.09)),3) for f in range(round(p['duration']*p['fps']))]
    (out/'mouth.json').write_text(json.dumps(mouth));(generated/'mouth.json').write_text(json.dumps(mouth))
    for name,x in [('voice',voice),('foley',foley),('music',music),('mix',voice+foley+music)]:wav(out/(name+'.wav'),x)
    # One encode from a float master. Loudness targets are verified rather than assumed.
    master=out/'master.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'mix.wav'),'-af','acompressor=threshold=0.16:ratio=2:attack=8:release=100,loudnorm=I=-14:TP=-1.8:LRA=9','-ar',str(SR),'-c:a','pcm_f32le',str(master)],check=True)
    l,tp=loudness(master)
    for attempt in range(3):
        if not np.isfinite(l) or l>=-14.4:break
        temp=out/'level.wav';gain=10**((-14-l+.2)/20)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(master),'-af',f'volume={gain},aresample=192000,alimiter=limit=0.8:level=false:latency=true,aresample={SR}','-c:a','pcm_f32le',str(temp)],check=True);temp.replace(master);l,tp=loudness(master)
    audio=out/'soundtrack.m4a';subprocess.run(['ffmpeg','-v','error','-y','-i',str(master),'-c:a','aac','-b:a','192k',str(audio)],check=True);l,tp=loudness(audio)
    report={'duration':p['duration'],'integrated_lufs':l if np.isfinite(l) else None,'true_peak_dbtp':tp if np.isfinite(tp) else None,'dialogue_cues':cues,'speech_time_stretched':False,'sources':[e.get('source') for e in p.get('sound',[])],'generated_service_calls':0,'review_note':'Listen to the full mix with picture. This report measures signals, not acting quality. Null loudness/peak denotes silence.'}
    (out/'audio-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['voice','sfx','mix']);parser.add_argument('project');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--generate',action='store_true');parser.add_argument('--replace',action='store_true');parser.add_argument('--line');a=parser.parse_args();path,p=load_project(a.project)
    try:
        if a.command=='mix':mix(p)
        else:
            if a.generate and a.dry_run:parser.error('Choose --generate or --dry-run')
            updated=generate(p,a.command,a.generate,a.replace,a.line)
            if a.generate:path.write_text(json.dumps(updated,indent=2))
    except urllib.error.HTTPError as e:
        # Do not print raw request headers or credentials.
        print(json.dumps({'http_error':e.code,'message':'Generation failed; no automatic paid retry. Check account permissions and credits.'}));sys.exit(2)
