# Production — entrée en lisière, lumière PMD séparée

Voir `renders/lisiere_pmd_v1/README.md` pour les liens de téléchargement et la description des six groupes. Une seule entrée livrée sur la dernière demande ; le guide de finale n’est pas une seconde carte livrée.

```sh
.venv/bin/python source/lisiere_pmd_v1/build.py
.venv/bin/python source/lisiere_pmd_v1/verify.py
.venv/bin/python source/lisiere_pmd_v1/release.py
.venv/bin/python source/lisiere_pmd_v1/serve.py --port 8012
```

Dépendances : Pillow, NumPy, SciPy et historique Git complet. Pas de réseau ni de nouvelle génération nécessaire pour reconstruire. `references.json` épingle les références visuelles ; `raws/archive.json` les huit bruts RGBA lossless au commit100e6878 (dont deux guides et la tentative d’arbres avec fond rejetée). Cinq générations réellement utilisées pour les cinq plans statiques. Pas de segmentation approximative de la composition unique en bandes. Le sol reste plein sous les éléments de décor, les rochers sont des groupes générés complets repositionnés aux pieds des arbres.

Les sources Red épinglées sont lues dans le ZIP inchangé du lot1. Le doublon de `native_sources.zip` dans le répertoire source a été supprimé uniquement après contrôle de son identité avec le membre déjà conservé dans ce ZIP ; les lecteurs V1 et leurs tests ont été adaptés.

## Budget et conservation des livrables

Le ZIP de calques et le grand WebP animé sont conservés bit à bit au commit **7253a42e**. Leurs chemins Git, liens publics directs, tailles et SHA-256 sont dans `release.json`. `release.py` les matérialise dans `.cache/lisiere_pmd_v1/releases/` ; le serveur fournit les anciennes URL logiques `/renders/lisiere_pmd_v1/...` avec les mêmes octets. Les PNG d’import ne sont ni perdus ni stockés sur un service externe : ils sont dans le ZIP versionné dans Git. Cela évite de dépasser le budget cumulatif du checkout tout en gardant le téléchargement pérenne sur GitHub.

Le build écrit ces deux gros résultats dans le cache, les autres petits résultats dans `renders/`. Leur reconstruction est comparée aux SHA de la livraison. Une modification future volontaire nécessite une **nouvelle publication d’assets et un nouvel index**, pas de remplacer silencieusement les blobs épinglés. Les livraisons antérieures et Beach restent inchangés ; conserver les stashes historiques.

## Portée des tests

Recomposition des cinq plans, transparence et couleurs, sol sans trous, superposition effective de plans indépendants, couloir central64px, dégagement conservateur8px, toutes les448combinaisons rayons/particules comparées à la source, six cascades ×8phases natives, boucles/cadences, CRC/PNG/basenames Ground8, assembleur autonome et historiques. Les tests de pixels ne définissent pas les collisions/warps PMDO et ne valent pas approbation artistique.

Racine du serveur : PNG direct, aucun HTML nécessaire. WebP et ZIP directs ; membres individuels du pack sous `/lisiere-pack/...`, notamment `/lisiere-pack/apercus/LE1_six_calques.png` pour voir les six groupes.
