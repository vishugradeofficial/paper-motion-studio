import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const studio=path.join(root,'studio');const require=createRequire(path.join(studio,'package.json'));
const {bundle}=require('@remotion/bundler');const {selectComposition,renderStill,renderMedia}=require('@remotion/renderer');
const [mode,filename]=process.argv.slice(2);
if(!['board','preview','render'].includes(mode)||!filename)throw new Error('Usage: node scripts/render.mjs board|preview|render path/to/project.json');
const projectPath=path.resolve(filename);const project=JSON.parse(fs.readFileSync(projectPath,'utf8'));const python=process.env.PYTHON||'python3';
execFileSync(python,[path.join(root,'scripts/project.py'),'validate',projectPath],{stdio:'inherit'});
execFileSync(python,[path.join(root,'scripts/audio.py'),'mix',projectPath],{stdio:'inherit'});
const out=path.join(root,'out',project.slug);fs.mkdirSync(out,{recursive:true});
const digest=crypto.createHash('sha256').update(JSON.stringify(project));
const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);
for(const filename of walk(path.join(studio,'src')))digest.update(filename.slice(studio.length)).update(fs.readFileSync(filename));
for(const audio of [...project.dialogue.map(d=>d.audio),...(project.sound||[]).map(e=>e.source)].filter(n=>n&&!n.startsWith('procedural:')))digest.update(audio).update(fs.readFileSync(path.join(studio,'public',audio)));
const hash=digest.digest('hex');const boardFile=path.join(out,'storyboard.json');
if(mode!=='board'&&(!fs.existsSync(boardFile)||JSON.parse(fs.readFileSync(boardFile)).projectHash!==hash))throw new Error('Render a current storyboard before animation: node scripts/render.mjs board '+filename);
const mouth=JSON.parse(fs.readFileSync(path.join(out,'mouth.json'),'utf8'));const inputProps={project};
process.chdir(studio);
const serveUrl=await bundle({entryPoint:path.join(studio,'src/index.ts'),publicDir:path.join(studio,'public')});
const composition=await selectComposition({serveUrl,id:project.composition||'PaperReel',inputProps});
if(mode==='board'){
 const board=path.join(out,'board');fs.mkdirSync(board,{recursive:true});
 for(const shot of project.shots){const frame=Math.round((shot.start+shot.end)/2*project.fps);await renderStill({serveUrl,composition,frame,inputProps,output:path.join(board,shot.id+'.png'),overwrite:true});}
 fs.writeFileSync(boardFile,JSON.stringify({projectHash:hash,shots:project.shots,reviewStatus:'Review full-size stills before animation'},null,2));
 execFileSync(python,[path.join(root,'scripts/sheet.py'),projectPath],{stdio:'inherit'});
 console.log('Storyboard: '+path.join(out,'storyboard.jpg'));
}else{
 const preview=mode==='preview';const frames=preview?Math.min(composition.durationInFrames,project.fps*8):composition.durationInFrames;let last=0;
 const raw=path.join(out,preview?'preview-silent.mp4':'picture-silent.mp4');
 await renderMedia({serveUrl,composition,inputProps,codec:'h264',outputLocation:raw,muted:true,frameRange:[0,frames-1],concurrency:3,crf:18,imageFormat:'jpeg',jpegQuality:94,x264Preset:'fast',overwrite:true,onProgress:p=>{if(Date.now()-last>12000||p.progress===1){last=Date.now();console.log(JSON.stringify({frames:p.renderedFrames,total:frames,percent:Math.round(p.progress*100)}));}}});
 const final=path.join(out,preview?'preview.mp4':project.slug+'-final.mp4');
 execFileSync('ffmpeg',['-v','error','-y','-i',raw,'-i',path.join(out,'soundtrack.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy','-t',String(frames/project.fps),'-metadata','title='+project.title,'-movflags','+faststart',final]);
 const info=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',final],{encoding:'utf8'}));const v=info.streams.find(s=>s.codec_type==='video');
 if(Number(v.nb_read_frames)!==frames||v.width!==project.width||v.height!==project.height||Math.abs(Number(info.format.duration)-frames/project.fps)>.08)throw new Error('Final frame or duration check failed');
 execFileSync('ffmpeg',['-v','error','-i',final,'-map','0:v:0','-map','0:a:0','-f','null','-']);
 const ledger=path.join(root,'work',project.slug,'credits.json');const costs=fs.existsSync(ledger)?JSON.parse(fs.readFileSync(ledger,'utf8')):[];
 const report={title:project.title,video:path.basename(final),duration:Number(info.format.duration),frames,width:v.width,height:v.height,fps:project.fps,decode:'passed',renderServiceCalls:0,knownProjectGenerationCredits:costs.reduce((n,x)=>n+(x.credits??0),0),unknownCreditEntries:costs.filter(x=>x.credits===null).length,audio:JSON.parse(fs.readFileSync(path.join(out,'audio-report.json'),'utf8'))};
 fs.writeFileSync(path.join(out,preview?'preview-report.json':'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}
