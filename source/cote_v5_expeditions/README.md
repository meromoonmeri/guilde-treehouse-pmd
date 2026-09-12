# Nouveau lot — sept falaises et trois entrées (en préparation)

**Aucun nouveau pack de dix cartes n’est encore livré.** L’étude des ressources est faite ; le moteur est maintenant installé depuis RUNTIMEPMDO, mais l’éditeur graphique plante encore. Vingt anciennes cartes ont passé la désérialisation native sans affichage.

- [Manuel des méthodes et limites](../../MANUEL_METHODE_PMDO.md)
- [Audit des trois références](audit/references.json)
- [Provenance des sources](references/provenance.json)
- [État de l’installation PMDO 0.8.12](installation_pmdo.json)

## Ce qui est étudié

Crooked Cavern (Palika/Halcyon) : Base, Objects, Shadows, cellules 8 px, carte 320×240.
Brine Cave (Explorers of Sky Origins) : feuille animée en 24 px, carte 648×504.
Drenched Bluff (Explorers of Sky Origins) : Background et Details, cellules 8 px, carte 528×408.

Les frames référencées par les trois Ground ont été résolues dans leurs vraies banques, à leur échelle d’origine. Les compositions et les calques du dossier `audit/` sont des **images d’étude**, pas des assets du nouveau pack.

La consigne utilisateur est de reprendre les layouts et comprendre leur construction, **pas leurs textures**. Les matières finales restent Métano ; la nuit conserve le filtre exact d’Abyss.

`guide_compositions.png` est un brouillon généré non conforme au nombre de panneaux demandé : douze panneaux et des numéros répétés. Ne pas le découper automatiquement ni utiliser ses pierres comme textures finales. La géométrie des dix futures cartes doit être spécifiée séparément.

## Reproduire l’audit

```sh
.venv/bin/python source/cote_v5_expeditions/audit_references.py
```

Le lecteur supporte les cellules 8 et 24 px, compare les hashes, valide chaque référence de frame et produit les statistiques de calques. Il déprémultiplie les pixels translucides pour les compositions d’étude Pillow ; cela ne remplace pas une capture GPU et peut entraîner un arrondi.

## Installation moteur

Le dépôt utilisateur `meromoonmeri/RUNTIMEPMDO` a permis de récupérer le binaire ; les ressources de base ont aussi été installées. Le moteur confirme la version 0.8.12.0. Le chargeur réel a désérialisé les vingt Ground du pack Métano/Abyss, sans GPU. Le lancement graphique reste en échec (code 139), donc ni rendu ni gameplay ne sont encore validés. Voir [le rapport runtime](../pmdo_runtime/README.md). Aucun nouvel envoi de ZIP n’est requis.

Les anciens packs sont conservés sans modification.
