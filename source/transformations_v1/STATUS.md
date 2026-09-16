# Pilot work in progress — 2026-09-17

Requested: Dynamax, species-specific Gigantamax, Terastallization and all canonical Tera Jewels, PMD visual quality and real Ground/Dungeon playability.

First demonstration subject: Charizard. Native Gigantamax Idle exists at SpriteCollab0006/0003 and has been downloaded with its credits. It is not an enlarged normal or Mega form. Reference pin3609a86be2a4c8ad7cf255bd2255f044daafe24f.

The first generated `gigantamax_charizard_column.png` is REJECTED: it drew a cartoon dragon in twelve cells instead of an isolated eight-frame VFX. Do not export it or label it canonical.

Crown visual research covers the canonical type descriptions; first animated art pilots are Fire/Water/Normal. Other crown types remain requested, not yet produced. No assertion of all-type coverage or all-species custom tuning.

Engine source inspected: RogueCollab/RogueEssence8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b. `DirSheet.Import` accepts PNG suffix `.NxM.png` as frame grid, or directory containing `DirData.xml` and sequential numbered PNG files. No fake `.dir` binaries will be written. `GROUND.PlayVFXAnim(BaseAnim, DrawLayer)` exists. Source inspection does NOT mean actual import or playback has passed. The historical PMDO runtime cache is absent in this current workspace.
