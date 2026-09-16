# Current checkpoint — 2026-09-17

## Delivered: three assembled Charizard visual pilots

`apercu_transformations_v1.html` and `exports/transformations_v1/README.md` are the current deliverable. Dynamax, true species-specific Gigantamax and Fire Terastallization each have eight 240-phase / eight-second transformation GIFs, plus eight separate eight-second hold loops: **48 final GIFs**. Generated VFX extraction/interpolation has now run. Seven transparent layers are paged for direction D; all other rendered directions are reproducible, not all exported as layers.

`build_sequences.py` assembles descending columns, independent density layers, branching lightning, rising particles, opaque swap pulse, depth-separated cloud orbits; Tera assembles growth, refraction, opaque facets, fracture, fragments, body-clipped highlights and a faceless crown. Native Gigantamax Idle comes from SpriteCollab 0006/0003 at pin 3609a86be2a4c8ad7cf255bd2255f044daafe24f, with its credits retained; one static body pose per direction. Normal Dynamax is a visual ×3 scale, not an engine size/collision change.

Checks executed: 168 opaque-swap cases; 1,920 body-surface clipping checks; 24 periodic endpoint checks; 48 decoded GIFs at exactly 8,000 ms; RGBA page geometry; original source hashes unchanged; five attachment unit tests. Seam deltas are reported separately: periodic closure is not artistic approval. Manual review of storyboards and all final Tera/Gmax directions performed; crown angles and occlusion remain provisional.

## Crown correction still binding

Accessories have no integrated head or face; front-gem eyes also removed as promised. Faceless variants intentionally differ from exact canonical jewels. Fire/Water static candidates have eight provisional manually assigned views; Normal generation failed, the remaining 17 static type crowns do not exist. Only Fire has an assembled transformation in this checkpoint.

Attachment uses exact single black head and white shadow markers, plus per-form/direction width and seat offsets. No whole-body-bounds fallback. Six local multisheet folders profiled: Charizard, Mega X, Gmax, Carapagos V5 and archived V2/V4. 1,072 local records: 1,012 proposals and 60 blocked poses; 336 selected crown placements rendered separately. This is not complete remote SpriteCollab coverage. Missing local action triples: Charizard 13, Mega X 12, Gmax 1. Per-frame manual overrides exist; horn/ear masks do not.

## Remaining gates

- **No actual PMDO Ground/Dungeon import/playback test** for these effects. Engine source inspection at RogueEssence 8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b is not runtime verification. No fake compiled `.dir` files.
- All-species anatomical and pre/post silhouette fitting, all-direction layer exports and runtime sequencing remain unfinished.
- Other Tera types, type-specific materialization and reversed transformations remain unfinished. Crown angle fidelity, face visibility and horn/ear depth need further art review.
- Generated components plus optical-flow inbetweens and procedural choreography are not 240 hand-drawn frames. The rejected first Gmax source `gigantamax_charizard_column.png` must never be used; corrected isolated VFX source is used instead.
- Preserve approved Carapagos portraits and canonical backgrounds. Deferred Carapagos final review, Zarude direction repair, rejected Stellar reconstruction and Mega Raichu X/Y identity/resource audits remain in the roadmap.
