# Visual and project guide

The master canvas is 1080 × 1920, 30 fps. A 1080-unit-wide SVG makes geometry independent of export size. Keep key content within x=90…990 and y=145…1680; these are conservative composition margins, not a promise that every platform's current UI is identical. Preview on the destination app.

Paper `#FAF9F5`, ink `#15171B`, blue `#3866D9`. Arial for direct headings and captions; Georgia italic for emphasis; Courier New for small editorial labels. Fonts fall back to local equivalents. No external font request is required; exact glyph metrics may vary by OS.

Each scene has one headline, one short emphasis line and one visual demonstration. Use 12–24 frames for card entrances, short staggered reveals and held readable endpoints. Do not animate every element constantly. Match cuts to thought changes and reserve a moment to understand the result. Let a cursor, underline or progress bar explain an action.

## JSON

`brand`: name, accent, paper, ink. `shots`: unique id, contiguous start/end in seconds, layout, heading, emphasis, note. Optional `items` overrides template labels, `details` overrides step descriptions, `answer` overrides the takeaway/typed answer, `cta` overrides the closing button. Hook has four items; steps, comparison and timeline have three. Keep headings under about 27 characters and emphasis under about 32 at the default size; visually check longer or translated text. Long body text needs wrapping or a scene layout edit.

Layouts: `map` connects an original brief card to three explanation cards; `hook` assembles scattered ideas; `prompt` types a short answer; `steps` staggers three steps; `compare` demonstrates an edit decision with illustrative bars; `timeline` shows picture beats and a schematic waveform; `finish` underlines an action and resolves to a checkmark. The waveform is an illustration, not an analysis of the actual voice.

`dialogue`: id, start/end, text, speaker, voiceId, model and optional audio path relative to studio/public. Supplied captions show the current phrase with active-word blue highlights from the original ElevenLabs character alignment. Each optional `dialogue[].words` item has text and absolute start/end seconds. Imported audio without alignment shows plain phrase captions. `sound`: id, start/end, source, gain, role; optional prompt and generateDuration for ElevenLabs. Local sources: procedural:click, procedural:bed, procedural:clock, procedural:rain. Every imported sound needs usable rights and provenance.

The included example is a starter, not a cloned layout pack. For a new topic, replace illustrative labels and script, then design any new visuals it needs. Change `Reel.tsx` for new diagrams, screenshot inserts, or exact word-level highlighting. Screen recordings and charts require their own source evidence; the studio does not invent product results.

## Background controls

`brand.grid` accepts kind (`grid`, `dots`, `none`), spacing in SVG units, opacity (0–1), lineWidth and color. The default light grid uses 72-unit cells, 1.2-unit lines and opacity 0.34; the earlier 0.17 grid was too faint at thumbnail size. A restrained top/bottom shade keeps the center clear. Set a shot's `theme` to `dark` for an ink background, blue emphasis and dotted pattern. The original styling was improved after three additional user-supplied screenshots showed a clearer light grid, connected cards and a dark word-linked timeline. Those reference screenshots are not included in the repository.
