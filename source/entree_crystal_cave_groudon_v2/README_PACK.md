# ECC2 — Grotte de cristal : arrivée de Groudon (colonnes de flamme)

- Carte : ECC1 à l'identique (calques copiés octet par octet, collisions relues dans le projet ECC1).
- VFX : 8 colonnes de flamme en arc autour du point d'arrivée (384,300) ; poses générées (référence `Dark_Crater_Pit_TDS.png`), réduites x1/3, palette de 16 couleurs ; lueur au sol et voile de chaleur tramés.
- 3 calques d'événement `lueur_sol`, `colonnes_flamme`, `ecran_chaleur` : 48 phases × 4 ticks (3,2 s), dernière phase vide, **Visible=false** au chargement.
- `init.lua` : `arrivee_legendaire()` les affiche pendant 192 ticks, puis les masque. **Non testé dans PMDO** (accès Lua à `Layers[i].Visible` et calage de la phase 0 à vérifier).
- Construction : `build.py` → `package.py` (lance les tests) → `apercu_entree_crystal_cave_groudon_v2.html`.
- runtime_tested=false, art_approved=false.
