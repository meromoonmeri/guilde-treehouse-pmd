# Texture prairie Sky Peak — surface 512×512 native

Surface d'herbe Sky Peak quiltée à **100% en tuiles 8×8 natives du GIF**
(zone prairie y≥120), méthode imitée de `zones_guidees` : vocabulaire
dédupliqué (442 motifs), sélection avec continuité des bords voisins,
jamais de rotation/recoloration. Touffes sombres natives (8 sprites).
**Pas de galets** : le GIF n'en contient aucun isolé (candidats = éclats
de falaise, abandonnés — voir build).

- `prairie_fond_512.png` : fond quilté seul (jour)
- `prairie_sky_512_jour.png` : + touffes
- `prairie_sky_512_nuit.png` : filtre Abyss exact
- `details/touffe_*.png` : 8 sprites natifs + bboxes en manifeste
- `PLANCHE_TEXTURE_NE_PAS_IMPORTER.png` : source/fond/jour/nuit + 2x
- `AUDIT_MES_GENERATIONS.md` : autopsie des 5 bruts générés

Vérifications (`verification.json`, PASS) : 4096 cellules ∈ vocabulaire,
sprites == GIF, recomposition exacte, nuit == Abyss. **Pixels uniquement.**

Limites : surface de texture (pas une scène), raccords quilting à apprécier
à 1×, pas de test PMDO/GPU. Reproduction :
`source/texture_prairie_sky_v1/{build,verify}.py`.
