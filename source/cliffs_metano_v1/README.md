# Production des falaises Métano V1

Livraison : [`renders/cliffs_metano_v1/`](../../renders/cliffs_metano_v1/README.md).

## Périmètre et méthode

Clarification utilisateur : « des cliff comme les images référencer qui ont permis de construire ces cliffs ». Quatre nouvelles compositions, non destructives : deux sprites isolés et deux zones de terrain. Pas de pont ni d’étang.

Lecture préalable : `AGENTS.md`, README principal, méthode du témoin magenta et des lots Caps/Terrasses V3–V4. Inspection de la scène canonique, du témoin, des vrais échantillons et du crochet droit. La méthode suivie est celle **des rendus générés référencés**, pas celle des Ground reconstruits en tuiles natives.

## Six appels d’image et leurs intentions

Tous les bruts sont conservés. Les quatre premiers appels ont été demandés en parallèle avec références.

| Brut | Consigne de composition | Références fournies |
|---|---|---|
| `01_cap_des_alizes.png` | Plateau isolé asymétrique, pointe gauche arrondie, retour concave à droite, un niveau, marges magenta | scène canonique + matière stricte V4 + crochet droit V4 |
| `02_balcon_du_levant.png` | Long balcon en croissant, grande aire à droite, retour ombré à gauche, marges magenta | mêmes références |
| `03_cirque_des_explorateurs.png` | Clairière basse bordée d’une falaise en fer à cheval, escalier droit, accès sud et nord | scène canonique + matière stricte V4 + témoin Métano |
| `04_terrasses_du_sillage.png` | Terrasse basse sud-ouest, volée centrale vers terrasse haute nord-est | mêmes références |
| `01_cap_des_alizes_corrige.png` | Retirer la petite tablette herbeuse de la concavité pour avoir une face continue, demander un grain plus fin | brut 01 + scène canonique + matière stricte V4 |
| `03_cirque_des_explorateurs_corrige.png` | Ouvrir l’accès nord, retirer le garde-corps diagonal et relier le pied de l’escalier au sol central | brut 03 + scène canonique |

Contraintes communes : herbe jaune-verte, strates ocre denses, ombres mauves, fine couronne irrégulière, vue PMD orthographique de trois quarts, fond magenta pur, pas de ciel/eau/arbres/bâtiment/texte. Ne pas remplacer la matière par du grès lisse, de gros blocs ou un chapelet de galets. Les prompts demandent approximativement 1536 × 1024, **dimensions réellement obtenues 1264 × 848** ; aucun redimensionnement forcé du terrain.

L’outil n’a pas parfaitement suivi les demandes : cap encore assez grossier, sable et banquette ajoutés aux terrasses, ouverture du mur central lors de la correction du cirque. Le nom final **Défilé** reconnaît ce changement. Ces faits sont inscrits dans le manifest, pas dissimulés par les tests de couleurs.

## Scripts

```sh
python -m venv .venv
.venv/bin/pip install -r source/cliffs_metano_v1/requirements.txt
.venv/bin/python source/cliffs_metano_v1/build.py
.venv/bin/python source/cliffs_metano_v1/verify.py
.venv/bin/python source/cliffs_metano_v1/package.py
node source/cliffs_metano_v1/test_viewer.cjs
.venv/bin/python source/cliffs_metano_v1/serve.py
```

Ouvrir `http://localhost:8000` depuis la machine qui exécute le serveur. Dans Arena, utiliser l’aperçu proxy du serveur. Le serveur écoute `0.0.0.0` et tous les liens du navigateur sont relatifs. `index.html` et l’aperçu racine fonctionnent aussi depuis le dépôt en fichiers locaux : manifest embarqué, pas de requête fetch obligatoire.

`build.py` réutilise explicitement `chroma` et `lab` de `source/caps_terrasses_v4/build.py`, la palette épinglée du même dossier et `night` d’Abyss. Les anciens fichiers ne sont jamais écrits. Il ne relance pas le générateur. Seuls les PNG de mer sont adaptés en nearest ; ciels/nuages/astres validés sont reconstruits sans resampling via `source/ciels_valides.py`. Le terrain conserve sa géométrie et ses dimensions de sortie.

`verify.py` reconstruit les échantillons canoniques depuis les deux banques `.tile`, vérifie les 328 couleurs, les empreintes, alpha, nuit, dimensions, noms uniques, les **huit recompositions ORA/PNG** et les **134 fichiers de contexte + deux bandes de nuages**. **60 contrôles PASS** au moment de la livraison. Aucun test de collisions, GPU ou gameplay.

`package.py` construit les deux points d’entrée de galerie et un kit compact : PNG terrains, ORA, contexte, planche, catalogue local, notice, manifest et rapports. Il n’inclut pas les bruts ni les scènes PNG redondantes, qui restent dans le dépôt. Le manifest y conserve leurs chemins de provenance.

`test_viewer.cjs` contrôle la logique avec un **DOM simulé** : quatre sélections, jour/nuit, liens de téléchargements, calques, zoom et préférence de réduction des mouvements. Syntaxe JavaScript vérifiée avec Node. Le téléchargement Chromium a échoué (connexion TLS au CDN), donc **pas de validation dans un vrai navigateur** revendiquée. Une vérification HTTP du serveur et des fichiers complète ces contrôles.

## Contraintes d’utilisation

- ORA à cinq calques de contexte/terrain ; pas de séparation artificielle de l’herbe, des couronnes et des faces.
- Pas de sol caché ni d’objet intégral reconstitué à partir d’une partition.
- PNG to Tileset : 8 px ; vérifier l’échelle visuelle avant utilisation. La divisibilité par 8 n’est pas une preuve d’échelle native.
- Aucun `.tile`, `.rsground`, index moteur, collision ou destination de donjon ajouté.
- Ces créations ne sont pas certifiées natives et attendent l’approbation utilisateur.

## Correction ciel/nuages

Les premiers fonds Caps/Terrasses étaient incorrects et ont été remplacés sur demande explicite. Sources validées c16efe12 : ciels jour/nuit, six familles de nuages et astres, sans agrandissement. La nuit des nuages emploie la formule Guilde/Sharpedo ; le terrain garde Abyss. Nuages en wrap1440px à−4px/s. Les PNG terrain restent inchangés ; scènes/ORA/ZIP/galerie sont reconstruits. Aucun mod ancien modifié.
