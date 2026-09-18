# Batch V7 — premier lot des 124 actions manquantes de la guilde

Priorité choisie par l'utilisateur : les animations de guilde manquantes (ordre fixé : manques des neuf membres → Team Dazzling → transition de combat → retour aux maps). Ce lot inaugure la ligne de production avec les deux familles d'actions qui ne demandent **aucune anatomie inventée ni masquage d'accessoire** :

- **Pain** : flinch assemblé depuis la feuille native `Hurt` (8 directions). Chaque frame est une copie translatée d'une frame native ; rien n'est recoloré ni redessiné.
- **DeepBreath** : respiration subtile assemblée depuis la feuille native `Idle` (8 directions), translation uniquement.

Six membres : Gardevoir, Canarticho, Pandespiègle, Balignon, Dimoret, Tarpaud (12 cycles, 8 directions chacun). Bagon/Draby, Ptiravi et Pachirisu ont déjà le profil natif complet : intacts.

Contrôles : `test_build.py` vérifie, pour chaque frame, que **tous les pixels visibles sont une copie translatée de la frame native épinglée** (provenance enregistrée dans `verification.json`), que les boucles ferment et que l'alpha reste binaire. Le précontrôle `validate.py` (dungeon) passe pour chaque pack. **Pas de validation artistique ni de test runtime PMDO.**

Reconstruire : `.venv/bin/python source/guild_scene_actions_v7/build.py` puis `test_build.py`.

Les registres sont mis à jour : `exports/guild_eat_all_v6/production_progress.json` et `PROGRESS.md` passent de 124 à **112 actions sans cycle local** ; `FULL_PROGRAMME_STATUS.json` (compteur guilde) est aligné à 112. Les crédits natifs sont copiés par pack (`*_native_credits.txt`), hors des dossiers d'export (exigence du validateur).

Ce ne sont pas des remplacements canoniques : Pain n'est pas un renommage de Hurt, c'est une chorégraphie distincte (flinch maintenu + tassement + retour) construite sur ses pixels ; les registres le déclarent comme stade technique.
