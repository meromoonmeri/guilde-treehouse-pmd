# Pilot work in progress — 2026-09-17

Requested: Dynamax, species-specific Gigantamax, Terastallization and all canonical Tera Jewels, PMD visual quality and real Ground/Dungeon playability.

First demonstration subject: Charizard. Native Gigantamax Idle exists at SpriteCollab0006/0003 and has been downloaded with its credits. It is not an enlarged normal or Mega form. Reference pin3609a86be2a4c8ad7cf255bd2255f044daafe24f.

The first generated `gigantamax_charizard_column.png` is REJECTED: it drew a cartoon dragon in twelve cells instead of an isolated eight-frame VFX. Do not export it or label it canonical.

Crown visual research covers the canonical type descriptions; first animated art pilots are Fire/Water/Normal. Other crown types remain requested, not yet produced. No assertion of all-type coverage or all-species custom tuning.

Engine source inspected: RogueCollab/RogueEssence8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b. `DirSheet.Import` accepts PNG suffix `.NxM.png` as frame grid, or directory containing `DirData.xml` and sequential numbered PNG files. No fake `.dir` binaries will be written. `GROUND.PlayVFXAnim(BaseAnim, DrawLayer)` exists. Source inspection does NOT mean actual import or playback has passed. The historical PMDO runtime cache is absent in this current workspace.

## Correction / attachment checkpoint — 2026-09-17

The earlier phrase “first animated art pilots are Fire/Water/Normal” described intent, not completed assets: **only Fire and Water crown candidates exist**, each with one static temporal frame in eight provisionally assigned/mirrored directions. Normal generation failed. The remaining 17 types are not produced.

Latest user requirement: independent accessories with **no integrated head or face**, fitted to the anatomical head of each existing sprite. Front-gem eyes have also been removed as promised; these deliberately faceless variants are not pixel-exact canonical jewels.

- `crown_attachment/`: explicit per-form/direction fit profiles, single black head and white shadow markers, CopyOf resolution and per-frame overrides. Missing/ambiguous markers and uncalibrated fall/roll poses block placement; no whole-body bounding-box fallback.
- Six local multisheet folders inventoried: Charizard, Mega Charizard X, Gigantamax Charizard and Carapagos V5, plus archived V2/V4. This does **not** cover the full remote SpriteCollab catalogue.
- 1,072 local frame-direction records: 1,012 fit proposals, 60 blocked. 336 placements rendered in selected previews; the others are not visually verified. Charizard/Mega X/Gmax still lack locally downloaded PNG triples for 13/12/1 declared actions respectively.
- Updated frontal/side seat offsets on the small forms. The upper ornament is now composited in front of the actor instead of disappearing behind Carapagos's shell; a lower band strip is behind the actor. This is a provisional depth convention, **not** horn/ear-specific occlusion masking.
- Build verifies source PNG hashes are preserved and seat arithmetic is consistent. Five mechanical unit tests pass (`.venv/bin/python -m unittest source.transformations_v1.crown_attachment.test_attachment -v`). No claim of anatomical approval follows from those tests.
- Review: `apercu_couronnes_attachees.html`; assets and detailed reports: `exports/crown_attachment_v1/`.

The corrected Gigantamax column source has been generated. `assets.py` contains extraction/interpolation support, but full `load_assets()` export and transformation choreography have not run. **No complete Dynamax/Gigantamax/Tera sequence, crown materialization, persistent body-crystal pass, or actual PMDO Ground/Dungeon import/playback validation is delivered at this checkpoint.** All remain required. Keep approved portraits and native sprite sources unchanged; preserve the deferred Carapagos/Zarude/Stellar/Mega Raichu X/Y queue.
