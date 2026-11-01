---
name: paper-motion-studio
description: Create vertical editorial motion-graphics explainers with paper grids, kinetic typography, UI diagrams, captions, speech and frame-timed sound. Use for original faceless tutorial reels and product explainers in this visual language.
---

# Paper Motion Studio

Read [the visual guide](references/visual-guide.md) for layout, timing and available scene templates. Read [reference coverage](references/reference-study.md) when comparing this studio with the supplied Instagram reels.

1. Turn the topic into one useful takeaway. Write an opening problem, a concrete demonstration and a small action the viewer can try. The included creator speaks in first person; use character dialogue when the story calls for it. Avoid unsupported product, psychological or performance claims.
2. Run `python scripts/project.py new my-topic --duration 36`. Edit the resulting JSON: contiguous shots, headings, blue italic emphasis, layout, scene content, dialogue and sound cues. Templates are editable starting points, not an automatic writer or a substitute for new illustrations. Add scene artwork in `studio/src/Reel.tsx` when the topic needs it.
3. Import licensed audio or use `scripts/audio.py voice PROJECT --dry-run`. New ElevenLabs generation uses account credits and requires `--generate`. Set the key in a local `.env` at this repository's root. Choose a voice, test a brief take before changing performance direction, then generate the rest. Keep delivery warm, conversational and unhurried. Adjust scene timing if the speech does not fit; never time-stretch it. Leave deliberate visual-only beats.
4. Run `python scripts/project.py validate PROJECT`, `npm --prefix studio run typecheck`, then `node scripts/render.mjs board PROJECT`. Inspect every full-size board frame for clipping, safe margins, caption overlap, legibility and diagram meaning. Show the board to the user before animating a new film. Fix and regenerate when needed.
5. After board review, run `node scripts/render.mjs render PROJECT`. Motion is a deterministic function of frame number; do not use random values, wall clocks or browser-only playback for animation. The renderer requires a board matching the current project.
6. Listen with picture: check voice clarity, pauses, effect attacks and music level. Audio measurements do not prove acting quality. Export `out/SLUG/SLUG-final.mp4`, captions, storyboard and reports; report exact known credits and any unknown charges honestly. Publishing to social media is a separate action.

`audio.py sfx PROJECT --dry-run` plans original ElevenLabs SFX from `sound[].prompt`; `--generate` creates them. Supplied sample clicks and music are procedural, not ElevenLabs recordings. Rendering never generates paid audio. Preserve references as links and analysis, not copied media, branding, avatar, scripts or soundtrack.
