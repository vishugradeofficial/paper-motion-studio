# One Clear Idea

A 36-second original editorial reel, 1080 × 1920 at 30 fps. The creator learns to cut an overloaded video down to one clear takeaway; the viewer's practical action is to write that takeaway in one sentence.

![Storyboard](storyboard.jpg)

[Video](one-clear-idea.mp4) · [Project JSON](project.json) · [Captions](captions.srt) · [Render report](render-report.json) · [Audio provenance](audio-provenance.json)

Six demo scenes: hook, prompt, connected-card map, comparison, dark word-linked timeline and closing action; the additional steps layout is also available. Voice: ElevenLabs Will, six original lines, 313 credits. Music and clicks: local synthesis. The example leaves deliberate visual-only holds and never speeds the voice. Reference audio/footage is not used. Listen with picture before posting.

From the repository root:

```bash
node scripts/render.mjs board examples/one-clear-idea/project.json
# After visual review:
node scripts/render.mjs render examples/one-clear-idea/project.json
```
