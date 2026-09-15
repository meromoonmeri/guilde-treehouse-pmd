# Terapagos Stellar — GIF previews

One GIF is provided for every animation index from `AnimData.xml`, including the `Strike` copy. Each preview shows PMD direction 0 (down/front) at native pixel size and loops continuously.

Timing is taken directly from the PMD animation data: one game tick is treated as 1/60 second. GIF delays are rounded to 10 ms and never go below 20 ms, the practical browser-safe minimum. Consecutive identical poses are merged with their delays added, so the visual timing stays unchanged without redundant GIF frames. The authoritative SpriteCollab sheets remain in `sprite/0186/`; these GIFs are only for visual review.

Regenerate from the repository root with:

```bash
python source/sprites_politoed/make_gifs.py
```
