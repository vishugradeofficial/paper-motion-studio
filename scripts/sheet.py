from pathlib import Path
import json,math,sys
from PIL import Image,ImageDraw,ImageFont
from common import ROOT
p=json.loads(Path(sys.argv[1]).read_text());out=ROOT/'out'/p['slug'];shots=p['shots'];w=360;h=685
im=Image.new('RGB',(w*3,math.ceil(len(shots)/3)*h),'#e7e8ec');draw=ImageDraw.Draw(im)
for i,s in enumerate(shots):
 x=i%3*w;y=i//3*h;im.paste(Image.open(out/'board'/(s['id']+'.png')).convert('RGB').resize((w,640)),(x,y));draw.text((x+12,y+650),f'{s["id"]} | {s["start"]:.1f}-{s["end"]:.1f}s | {s["layout"]}',fill='#222222')
im.save(out/'storyboard.jpg',quality=94)
