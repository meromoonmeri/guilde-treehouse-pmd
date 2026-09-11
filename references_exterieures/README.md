# Layouts extérieurs PMD — générés, multicouches et animés

Cette livraison applique le workflow extérieur audité, et non le workflow fixe
plus limité des salles de `main` : **native complète → pack de plans sources
RGBA sémantiques → composition contrôlée → timeline Aseprite, atlas Tiled et
aperçu animé**. Comme `source/sharpedo/` de la branche auditée, le constructeur
ne redécoupe jamais une composition : il charge les PNG nommés déjà préparés.

Les cinq images ajoutées le 11 septembre 2026 sont des **guides de layout**.
Les six layouts initiaux sont des rendus produits par le générateur d’images de
cette livraison, conservés dans `source/references_exterieures/generation/`.
Les six vrais backplates `00_ciel` sont eux aussi produits par des appels
séparés du générateur et conservés dans
`source/references_exterieures/generator_planes/`. Aucun pixel des références
externes n'est collé dans les natives ou les plans. Le script de préparation
réduit ces rendus entiers au plus proche voisin, crée
le pack explicite `source/references_exterieures/plans/<scene>/<ambiance>/`
et consigne les empreintes SHA-256 dans
`source/references_exterieures/provenance.json`.

## Scènes et tailles de production

| Identifiant | Intention du layout | Native | Ambiances |
| --- | --- | ---: | --- |
| `cascades` | îlot suspendu, cascades, bassin et rive | 408 × 648 px | Jour, nuit |
| `prairie_maritime` | prairie fleurie, retours rocheux et mer | 688 × 384 px | Jour, nuit |
| `cap_cotier` | prairie, maison-courrier, falaise et océan | 688 × 384 px | Jour, nuit |

La nuit est un rendu généré séparément à partir de son équivalent de jour afin
de préserver le même cadrage ; ce n'est pas un filtre appliqué au runtime.

## Plans éditables, du fond vers l'avant

### `cascades` — 7 PNG par ambiance

1. `00_ciel` : ciel reconstitué sous les éléments atmosphériques et montagnes lointaines ;
2. `01_astres` : lune immobile et étoiles nocturnes scintillantes (transparent le jour) ;
3. `02_nuages` : bancs de nuages défilants ;
4. `03_eau_cascades` : eau et profondeur des chutes ;
5. `04_cascades_ecume` : crêtes lumineuses et cascades animées ;
6. `05_ilot_rocheux` : îlot suspendu ;
7. `06_vegetation` : roseaux, buissons et avant-plan.

### `prairie_maritime` — 8 PNG par ambiance

1. `00_ciel` ; 2. `01_astres` ; 3. `02_nuages` ; 4. `03_mer_reflets` ;
5. `04_vagues_reflets` ; 6. `05_falaises` ; 7. `06_prairie_chemin` ;
8. `07_fleurs_vegetation`.

Le ciel de cette composition est dégagé : `02_nuages` est volontairement un
plan transparent, sans faux nuage ni atlas vide. La lune et les étoiles de nuit
restent un vrai plan animé.

### `cap_cotier` — 8 PNG par ambiance

1. `00_ciel` ; 2. `01_astres` ; 3. `02_nuages` ; 4. `03_mer_reflets` ;
5. `04_vagues_reflets` ; 6. `05_falaise_terrain` ; 7. `06_maison` ;
8. `07_vegetation`.

## Contrat de l’animation

Toutes les variantes utilisent une boucle de **24 images de 250 ms**, soit
**6 000 ms**. Les PNG dans `calques/` sont exactement l’**image 0** de chaque
plan ; `compositions/<ambiance>.png` est exactement la native préparée.

- Les `02_nuages` non vides sont décalés horizontalement d’un pixel à chaque
  phase et bouclent après 24 px.
- Pour chaque nuit, `01_astres` comporte des groupes de composantes. Les étoiles
  changent d'opacité selon une LUT de 24 phases ; le plus grand groupe (la lune)
  reste à 100 %, donc ne scintille pas.
- `04_cascades_ecume` ou `04_vagues_reflets` est un overlay de crêtes séparé du
  plan d'eau. Il reprend le cycle léger 24 phases (`dx`, `dy`, opacité) du
  workflow `sharpedo` et se boucle au même instant que nuages/étoiles.
- Un ciel sous-jacent est inpainté sous les éléments mobiles. Il n'apparaît pas
  dans le rendu initial, car les pixels atmosphériques originaux le recouvrent,
  mais évite de révéler un trou transparent lorsque les nuages se déplacent.
- Les plans de terrain restent des PNG indépendants. Ils sont séparés par rôle,
  pas artificiellement transformés en une animation sans contenu.

Cette nécessité d'un fond révélé signifie que les plans atmosphériques peuvent
se superposer au ciel à l'image 0. Le contrat contrôlé est l'identité stricte de
la recomposition avec la native, et non une fausse promesse de plans totalement
disjoints à chaque pixel.

## Arborescence d’une scène

```text
references_exterieures/<scene>/
├── calques/{jour,nuit}/     # PNG RGBA pleine taille, image 0
├── animations/              # groupes d'étoiles + atlas Tiled des plans mobiles
├── compositions/            # image 0 recomposée, strictement identique à la native
├── bases/                   # plans terrain seulement, transparente et magenta
├── aseprite/                # 24 images, calques réels, tag de boucle et cels liées
└── tiled/                   # image layers fixes + objets tuiles animés, grille 8 px

source/references_exterieures/plans/<scene>/{jour,nuit}/
└── 00_ciel.png …            # sources natives des mêmes plans, chargées par le build
```

Dans Tiled, les plans fixes sont des `imagelayer`. Les plans animés sont des
`objectgroup` pointant vers un atlas PNG : la tuile 0 contient une séquence de
24 entrées de 250 ms. Les cartes sont des aides de montage ; elles ne fournissent
ni collisions, ni transitions, ni autotiling. `bases/*_transparente.png` et
`bases/*_magenta.png` servent à contrôler l'extraction des plans de terrain.

## Reconstruction et contrôle

```bash
pip install -r source/requirements.txt
python source/prepare_references_exterieures.py
python source/rebuild_references_exterieures.py
python source/verify_references_exterieures.py
python source/verify_pmd.py
```

1. `prepare_references_exterieures.py` valide les dimensions/alpha des six
   rendus générés, prépare les natives **et le pack explicite de PNG sources
   par plan**, puis met à jour leur provenance.
2. `rebuild_references_exterieures.py` charge uniquement ce pack préparé,
   crée les exports PNG/Aseprite/Tiled et génère l'aperçu hors ligne. Il ne
   repartitionne aucun pixel d'une composition finale.
3. `verify_references_exterieures.py` relit les PNG, vérifie d'abord que
   chaque plan livré est identique à sa source préparée, puis valide l'identité image
   0/native, les périodes, les pixels des cels Aseprite, les cels liées, les
   atlas et séquences Tiled, les bases, les deux ambiances et l'autonomie HTML.
4. `verify_pmd.py` reste le contrôle indépendant du kit historique de `main`.

Ouvrir [`../apercu_references_exterieures.html`](../apercu_references_exterieures.html)
pour changer de scène/ambiance, mettre en pause, masquer un plan et afficher
ou masquer la **grille de 8 × 8 px** (visible par défaut). Les images y sont
encodées en WebP data URI : aucune requête réseau n'est requise.

L’analyse détaillée de la branche précédente — notamment sa chronologie et sa
mécanique `exterior_animation.py` — est dans
[`../AUDIT_BRANCHE_01A082DB.md`](../AUDIT_BRANCHE_01A082DB.md).
