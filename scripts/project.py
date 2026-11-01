from pathlib import Path
import argparse,json,math,re,shutil,subprocess,sys
from common import ROOT,asset
CAMERAS={'hook','prompt','steps','compare','timeline','finish','map'}
def validate(p):
    errors=[]
    for name in ['slug','title','duration','fps','width','height','shots','dialogue']:
        if name not in p:errors.append(f'Missing {name}')
    if errors:return errors
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',str(p['slug'])):errors.append('Invalid slug')
    for k in ['duration','fps','width','height']:
        if not isinstance(p[k],(int,float)) or isinstance(p[k],bool) or not math.isfinite(p[k]) or p[k]<=0:errors.append(f'{k} must be positive and finite')
    if errors:return errors
    if p['width']%2 or p['height']%2:errors.append('Video dimensions must be even')
    if p['fps']!=int(p['fps']):errors.append('Use an integer fps')
    if abs(p['duration']*p['fps']-round(p['duration']*p['fps']))>1e-6:errors.append('Duration must contain a whole number of frames')
    if any(p[k]!=int(p[k]) for k in ['width','height']):errors.append('Video dimensions must be integers')
    if not p['shots']:errors.append('At least one shot is required')
    brand=p.get('brand',{})
    for k in ['accent','paper','ink']:
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}',str(brand.get(k,''))):errors.append('Brand '+k+' needs a six-digit hex color')
    for s in p['shots']:
        if any(not isinstance(s.get(k),(int,float)) or isinstance(s.get(k),bool) or not math.isfinite(s[k]) for k in ['start','end']):return errors+['Shot times must be finite']
        for k in ['heading','emphasis']:
            if not isinstance(s.get(k),str) or not s[k].strip():errors.append('Shot '+k+' is required')
        if s.get('items') is not None:
            expected=4 if s.get('layout')=='hook' else 3
            if not isinstance(s['items'],list) or len(s['items'])!=expected or not all(isinstance(x,str) for x in s['items']):errors.append('Template item count is invalid')
    end=0;ids=set()
    for s in p['shots']:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',str(s.get('id',''))):errors.append('Shot id must be a safe filename')
        if s.get('id') in ids:errors.append('Duplicate shot id')
        ids.add(s.get('id'))
        if abs(s.get('start',-1)-end)>.001:errors.append(f'Shot {s.get("id")} leaves a gap or overlaps')
        if s.get('end',0)<=s.get('start',0):errors.append('Shot must have positive duration')
        if s.get('layout') not in CAMERAS:errors.append(f'Unsupported layout {s.get("camera")}')
        end=s.get('end',0)
    if abs(end-p['duration'])>.001:errors.append('Shots must cover the whole film')
    ids=set();intervals=[]
    for d in p['dialogue']:
        if d.get('id') in ids:errors.append('Duplicate dialogue id')
        ids.add(d.get('id'))
        if not isinstance(d.get('text'),str) or not d['text'].strip():errors.append('Dialogue text is required')
        if not 0<=d.get('start',-1)<d.get('end',0)<=p['duration']:errors.append('Dialogue interval outside film')
        if d.get('audio'):
            try:
                a=asset(d['audio'])
                if not a.exists():errors.append(f'Missing audio: {d["audio"]}')
                else:
                    seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(a)]))
                    if seconds>d['end']-d['start']+.08:errors.append(f'Dialogue {d["id"]} is longer than its slot; revise timing, not speech speed')
            except (ValueError,subprocess.CalledProcessError):errors.append('Invalid audio path or file')
        intervals.append((d.get('start',0),d.get('end',0),d.get('id')))
    for a,b in zip(sorted(intervals),sorted(intervals)[1:]):
        if b[0]<a[1] and not p.get('allowDialogueOverlap',False):errors.append(f'Dialogue slots overlap: {a[2]} and {b[2]}')
    for e in p.get('sound',[]):
        if not 0<=e.get('start',-1)<e.get('end',0)<=p['duration']:errors.append('Sound event outside film')
        if e.get('source') and not e['source'].startswith('procedural:'):
            try:
                if not asset(e['source']).exists():errors.append('Missing sound asset: '+e['source'])
            except ValueError as ex:errors.append(str(ex))
    return errors
if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');v=sub.add_parser('validate');v.add_argument('project');n=sub.add_parser('new');n.add_argument('slug');n.add_argument('--duration',type=int,default=120)
    a=parser.parse_args()
    if a.command=='doctor':
        status={name:bool(shutil.which(name)) for name in ['node','npm','ffmpeg','ffprobe']};status['python']=sys.version.split()[0];print(json.dumps(status,indent=2));sys.exit(0 if all(status.values()) else 1)
    if a.command=='new':
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',a.slug) or a.duration<4:parser.error('Use a lowercase slug and a duration of at least four seconds')
        folder=ROOT/'projects'/a.slug;folder.mkdir(parents=True,exist_ok=False)
        p=json.loads((ROOT/'examples/one-clear-idea/project.json').read_text());ratio=a.duration/p['duration'];p.update(slug=a.slug,title=a.slug.replace('-',' ').title(),duration=a.duration,dialogue=[],sound=[])
        for s in p['shots']:s['start']=round(s['start']*ratio,3);s['end']=round(s['end']*ratio,3)
        (folder/'project.json').write_text(json.dumps(p,indent=2));print(folder/'project.json')
    else:
        errors=validate(json.loads(Path(a.project).read_text()));print(json.dumps({'valid':not errors,'errors':errors},indent=2));sys.exit(bool(errors))
