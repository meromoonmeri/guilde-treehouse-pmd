# Zone D06P11 V11 — verdoyante, multicalque, textures canoniques
Layout **identique à V10**. Seul changement de géométrie : le **second chemin vers la grotte** (ancien goulet de 5 cases entre deux lèvres rocheuses, rangées 41-50) est ouvert en rampe de 13 cases, sans bordure ni décor.
Le guide régénéré `generation/guide_verdoyant_REJETE.png` (escalier de verdure ajouté) a été **rejeté** et n'est pas utilisé.

## Calques terrain (ordre)
| Calque | Source des pixels |
|---|---|
| `05_falaise_d06p11a` | tuiles ROM d06p11a exactes, massif complet (faces cachées sous l'herbe), grotte ROM + couture |
| `06_herbe` | tuiles d05p11a (Apple Woods) exactes : herbe claire en lisière du chemin, herbe sombre ailleurs |
| `07_chemin` + `07b_bord_chemin` | tuiles de chemin d05p11a exactes ; bord 1 px = couleur de chemin la plus sombre de d05p11a |
| `08_lisere_herbe` | 1 px, couleur d'herbe sombre existante de d05p11a |
| `10_rochers_d13p11a`, `12_cailloux_d13p11a` | piliers/cailloux découpés de d13p11a (pixels exacts) |
| `11_fleurs_d05p11a` | touffes de fleurs découpées de d05p11a |
Références : `references/d05p11a.png`, `references/d13p11a.png` (aperçus du repo PMD-SKY-PMDO-PORT, noms SkyTemple).
Non canonique : forme des masques (layout), choix des cases (correspondance de motif), placement du décor. Crépuscule/nuit = étalonnage.

## Astres
- Jour : soleil blanc tramé façon Sky (inchangé).
- Crépuscule : **soleil couchant généré** style Colline des Anciens (`generation/soleil_crepuscule_frames.png`, 8 frames × 8 f).
- Nuit : lune V7.
Mer, berge à la Métano, nuages : repris de V10. Collisions : 1302 cases (bases des piliers bloquantes). Non testé en jeu.
Construction : `falaise_canon.py` → `sol_canon.py` → `build.py`.
