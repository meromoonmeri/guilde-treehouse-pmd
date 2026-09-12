# Inventaire PMUniverse — lecture et réutilisation

Cet annuaire est le résultat de l’audit exhaustif daté du **13 septembre 2026** (fuseau Europe/Paris) des dépôts publics de l’organisation [`PMUniverse`](https://github.com/PMUniverse). Il catalogue les actifs et les conteneurs graphiques **sans recopier leurs pixels** dans ce projet.

## Fichiers livrés

| Fichier | Rôle |
|---|---|
| [`manifest.json`](manifest.json) | Source de vérité : dépôts, commits immuables, licences déclarées par dépôt, 2 241 fichiers concernés, URL GitHub/RAW épinglées, taille, SHA-1 de blob Git et SHA-256 des octets récupérés. |
| [`inventory.csv`](inventory.csv) | Même catalogue, une ligne par fichier, pratique pour tableur/filtrage. |
| [`container_analysis.json`](container_analysis.json) | Analyse sans extraction persistante des PNG inclus dans les `.tile`, `.sprite` et `.portrait`, et dimensions des PNG directs. |
| [`summary.json`](summary.json) | Agrégats par dépôt, format et archive examinée. |
| [`../AUDIT_PMUNIVERSE_ASSETS.md`](../AUDIT_PMUNIVERSE_ASSETS.md) | Rapport humain : couverture, résultats, formats, licences et limites d’usage. |

Les URL de chaque ligne utilisent le **commit audité**, et non une branche mouvante. `git_blob_sha1` est le hachage Git fourni par l’arbre récursif ; `sha256` est le hachage de l’octet-à-octet des clones locaux vérifiés au même commit.

## Reproduire l’inventaire

Le script ne télécharge aucun pixel par défaut : il ne consulte que l’API GitHub. Pour régénérer les SHA-256 et l’analyse interne des conteneurs, fournir des clones à la révision que l’API vient d’auditer :

```bash
mkdir -p .cache/pmuniverse-audit/clones
for repo in Installer Updater Scripts framework PMU-Client PMU-Server; do
  git clone --depth 1 "https://github.com/PMUniverse/${repo}.git" ".cache/pmuniverse-audit/clones/${repo}"
done
python3 source/audit_pmuniverse_assets.py \
  --audit-date 2026-09-13 \
  --checkout-root .cache/pmuniverse-audit/clones \
  --out audit_pmuniverse_assets
```

Le script compare le `HEAD` de chaque clone au commit provenant de l’API et s’arrête si l’un d’eux diffère. Il s’arrête aussi si GitHub annonce un arbre récursif tronqué ; il ne peut donc pas produire silencieusement un faux inventaire exhaustif.

> Les clones d’analyse doivent rester sous `.cache/`, qui est ignoré par Git. Les actifs PMUniverse ne sont pas ajoutés au kit de falaise ni réexportés par ce dépôt.

## Portée de `scope`

- `direct_visual` : PNG, ICO et sources Paint.NET directement présents ;
- `visual_container` : `.tile`, `.sprite`, `.portrait` PMU qui renferment des flux PNG ;
- `typography` : fontes ;
- `map_data` : sérialisations de cartes faisant référence aux tuiles, et non des pixels directement réutilisables ;
- `resource_descriptor` : `.resx` .NET examinés afin de ne pas manquer une ressource embarquée ;
- `archive_review` : archive analysée au niveau de son répertoire central.

La présence d’une URL de récupération est une information de provenance, **pas une autorisation de redistribution**. Lire le rapport de licences avant toute réutilisation.
