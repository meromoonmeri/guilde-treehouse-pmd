# Plage animée V2 — statut

Demande : « le générateur fait plusieurs calques : eau animée palette cycling
canoniquement / sable / roche / etc. »

## Livré

- `renders/plage_animee_v2/` : 4 statiques, 16+16 phases eau, 16 scènes,
  WebP/GIF, ORA 36 calques, planche, manifeste.
- ZIP `renders/plage_animee_v2_pack.zip`, viewer `apercu_plage_animee_v2.html`.
- 10 tests PASS. PMDO NON TESTÉ, art non approuvé. V1 intacte.

## Points techniques

- 3 textures générées (mer/sable/roche) + masques V1 byte-exacts.
- Eau : index 16 + 16 LUTs rotation +1, 60 ms, boucle exacte, transitions
  12.5–14.1 toutes phases. Dérive : x côtés (signe vers la rive), y nord.
- Écume : géométrie V1, 4 niveaux, 16 LUTs sinus, p10/p98 + blanc franc.
- Corrections en cours de route : PNG indexé en L (le P sans palette est
  réaplati par Pillow) ; rampe unique 16 (2×8 donnait une rampe profonde
  plate) ; 16 phases (8 phases sur 16 entrées ne bouclaient pas) ;
  dégradés p2→p98 (médianes effondrées sur art deux tons).
- Sandbox réinitialisée pendant le lot (5e fois, venv + historique local
  perdus) : réintégration ff-only depuis le remote (commits V1 intacts),
  venv reconstruite. Cf. notes V7/V13/V14 dans AGENTS.md.

## Registre

Registre natif sud–nord inchangé (lot généré, pas relayout natif).
