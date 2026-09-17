# Ledian Dojo — trois couloirs et trois salles souterraines

Galerie autonome : **`apercu_ledian_dojo_v1.html`** à la racine. [Planche des six variantes](PLANCHE.png).

## Variantes vides
| Pièce | Accès |
|---|---|
| Couloir nord–sud élargi | Nord, sud |
| Couloir est–ouest | Est, ouest |
| Jonction en T | Nord, est, ouest |
| Salle traversante | Nord, sud |
| Salle latérale | Ouest, sud ; échelle native facultative au fond |
| Salle carrefour | Nord, sud, est, ouest |

**512×512 par pièce**, sans mobilier, personnage, tapis ni brasero. Les jambages de certains passages sont structurels. Le couloir nord–sud est un passage élargi avec palier, pas un étroit boyau.

## Méthode retenue
Vraie référence Halcyon téléchargée et reconstruite → génération de variantes guidée par la carte et ses feuilles de sol/roche → inspection → nouvelles passes de correction des accès → détourage → raccords et calques → vérification.

Les matières de référence sont la roche brun-gris arrondie et stratifiée, les petites dalles irrégulières et la terre ocre du sous-sol de Ledian. Pas de bois de café ni de nouvelle roche bleue. Les propositions sont des **images générées guidées par ces ressources**, comme la méthode Northern ; elles ne sont pas des cartes natives pixel-identiques. Les bruts sont conservés dans `bruts/`, y compris les deux premiers essais remplacés par les fichiers `_corrige`.

Le générateur avait laissé des trous magenta dans certaines bouches de passage. Deux nouvelles passes ont corrigé le nord–sud et le carrefour ; un même patch de sol canonique sert ensuite de bande de raccord contrôlée.

## Calques
Chaque dossier de pièce contient :
1. `01_sol_chemin.png`
2. `02_murs_fond.png`
3. `03_roche_gauche.png`
4. `04_roche_droite.png`
5. `05_roche_premier_plan.png`
6. Un `06_acces_N/S/E/W.png` **par accès**, indépendant.
7. Sur la salle latérale uniquement : `07_echelle_native.png`, désactivé par défaut.

Puis `composition.png`, `terrain_detoure.png` et `schema.png`. **46 calques alignés au total**, tous sur512×512 et placés en(0,0).

Les cinq calques de terrain sont des partitions de surfaces visibles. Leur recomposition redonne exactement le terrain détouré. Ils ne reconstruisent pas le dessous des parois, et leurs frontières sont des découpes de travail : pas des classifications automatiques parfaites de chaque pierre, ni des volumes déplaçables sans retouche.

## Entrées / sorties
**15 ports de64px**, centrés sur les bords correspondants. Les coordonnées et directions sont dans `manifest.json` et sur les schémas.

Leur première bande de sol est opaque et identique, à orientation de raccord équivalente : cela évite un vide alpha au passage. Le calque de raccord utilise l’extrait natif `Ledian_Dojo_Floor.png` (184,224)-(216,256), agrandi×2 sans lissage. Il est opaque côté bord et s’atténue vers l’intérieur. Le patch non agrandi est fourni dans `materiaux/sol_raccord_natif.png`.

**La bande commune ne garantit pas que toute la silhouette rocheuse s’emboîte sans retouche.** Certains passages ont un dégagement visuel plus large que le port de64px. Une courte zone de transition peut rester nécessaire selon l’assemblage retenu. Il ne s’agit pas de transitions PMDO codées ni d’un test de navigation/collision.

L’échelle provient directement de la couche native Objects Over, boîte (192,48)-(216,120), sans changement des pixels. Son sprite original est dans `materiaux/echelle_native.png`. Elle est proposée séparément sur la paroi nord de la salle latérale ; sa destination en jeu n’est pas implémentée.

## Source exacte
[Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit **da6c2130d641507447e6386a5e47a296e8cb4c71** :
- `Data/Ground/ledian_dojo.rsground`, carte408×312, grille8px ;
- sept banques `Ledian_Dojo_{Animated,Ceiling,Floor,Objects,Objects_Over,Objects_Under,Shadows}.tile`.

Sources, feuilles décodées, six couches visibles reconstruites, référence composée et SHA256 : `source/ledian_dojo_v1/references/`. Le bouton Référence native montre la vraie carte meublée, à distinguer des variantes vides livrées.

Les ressources sont attribuées à leurs auteurs/contributeurs et ayants droit concernés. Leur présence dans un dépôt public ne vaut pas licence générale de redistribution libre.

## Vérifications et reproduction
`verification.json` : sources SHA256 inchangées, six compositions exactement recomposées,46 calques512×512, échelle et patch égaux aux extraits natifs. Le build vérifie les15 ports opaques et leur bande commune. Galerie : six scènes, calques, échelle optionnelle, schémas et référence vérifiés en DOM simulé.

Scripts dans `source/ledian_dojo_v1/` : `inspect_sources.py`, `build.py`, `gallery.py`, `verify.py`, `test_viewer.cjs`. Pillow et numpy ; `gh` pour récupérer les sources si absentes.

**Rendus statiques, pas d’animation ni de validation PMDO.** Aucun nouveau `.rsground` livré. Les anciens packs café, falaises et Northern sont conservés.
