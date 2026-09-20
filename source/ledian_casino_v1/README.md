# Casino Ledian — réseau, terrain préservé et objets PMD indépendants

## Demande actuelle — remplace l’interdiction de décoration précédente

L’utilisateur a renvoyé visuellement sa première proposition de salle : grande pièce de pierre, parois rocheuses brun-gris, sol dallé continu et entrée au sud. Il demande maintenant **un réseau de casino sur le terrain Ledian**, avec **tapis rouges, estrades, rideaux, mobilier et kiosques sur des calques distincts**, inspirés des objets de Métano/Halcyon, particulièrement la structure liée à Murkrow.

Conserver une base de terrain vide ; ajouter l’aménagement en overlays réversibles. « Sans déco » reste donc valable pour la base, **pas pour les calques optionnels nouvellement demandés**. Ne jamais cuire le tapis, le rideau ou un meuble dans le sol. Les bordures rocheuses doivent accompagner les jambages de chaque entrée, sans rocher qui coupe le passage.

## Référence native réellement retrouvée : Krow Bank

Source : [Palikadude/Halcyon](https://github.com/Palikadude/Halcyon), commit `da6c2130d641507447e6386a5e47a296e8cb4c71`.

- `Data/Script/ground/metano_town/init.lua`, lignes2837/2849 : `Bank_Owner` est Murkrow.
- `Data/Script/ground/metano_town/metano_town_ch_2.lua`, lignes460–466 : visite de **Krow Bank**, stockage de l’argent auprès de Murkrow.
- `Content/Tile/Metano_Town_Objects.tile` : coiffe/toiture noire avec motif de bec doré.
- `Content/Tile/Metano_Town_Objects_Over.tile` : guichet et coffres qui complètent la structure.
- La zone correspondante de `Objects_Under` ne fournit pas le corps de cette structure.

Extraits natifs dans `references/`, sur canevas alignés **104×96**, grille8px :

1. `KrowBank_toiture_native.png` ;
2. `KrowBank_guichet_native.png` ;
3. `KrowBank_structure_native.png`, recomposition de contrôle.

Aucun redimensionnement, recoloration, miroir ou redessin des pixels dans ces extraits. Fenêtre source `(976,928)–(1080,1024)` ; la toiture conserve seulement les48premières lignes pour exclure les éléments de rue sans rapport. Les positions et hashes sont dans `provenance_krow_bank.json`. Ces fichiers sont **des références d’objets**, pas une salle de casino finie. Attribution aux auteurs/contributeurs de Halcyon et ayants droit PMD ; disponibilité publique ne signifie pas licence générale de redistribution libre.

Reproduire l’étude : `.venv/bin/python source/ledian_casino_v1/inspect_krow_bank.py` (Pillow, NumPy et `gh`). Identité Git des banques contrôlée contre le commit épinglé ; aucun runtime PMDO testé.

## Réseau proposé — plan de travail, pas maps déjà produites

Quatre modules raccordables, à adapter à la salle choisie :

```text
Scène / estrade ───── Salon
      │                │
Accueil / change ── Salle de jeux
      │
   Entrée
```

La salle choisie sert de référence de matière et de volume. Les ouvertures supplémentaires et leurs retours rocheux sont à traiter explicitement ; ne pas coller une bande de sol par-dessus un mur fermé et annoncer le raccord terminé.

### Calques prévus

- Terrain : sol, parois du fond, bordures gauche/droite, premier plan, raccord par entrée.
- Textiles : tapis rouge et ses branches ; tentures/rideaux séparés.
- Scène : estrade, marche et façade ; rideaux indépendants de l’estrade.
- Structures : kiosque de change, guichet d’accueil et éventuelles échoppes PMD, sous forme d’objets détourés complets, pas de bâtiments peints dans le terrain.
- Mobilier : tables, sièges et accessoires sur des calques/instances dédiés.

Prévoir une origine, une emprise au sol et un ordre d’affichage par structure. Les objets pourront être déplacés ou masqués sans abîmer le sol ; préserver les passages entre les salles. Le style de Krow Bank sert de référence de proportions et de construction, pas d’autorisation à modifier silencieusement les ressources natives.

## État exact et blocage de la pièce jointe

Le guide initial `guides/layout.png` n’est pas l’image choisie et ne doit pas la remplacer. Les anciennes propositions du comparateur n’avaient pas été enregistrées.

L’image est maintenant **visible dans le message utilisateur**, annoncée au chemin `/home/user/uploads/image-1.png`. Toutefois, ce fichier n’existe pas dans le filesystem accessible aux outils lors de cette reprise (`read_file` et recherches dans `/home/user`, `/tmp`, `/mnt` négatifs). Ne pas affirmer qu’elle a été chargée, détourée ou corrigée. Il faut récupérer effectivement ce fichier pour une édition fidèle de la salle ; ne pas la recréer approximativement sous prétexte de conserver l’original.

**Livré à ce stade : étude native, deux calques d’objet de référence et plan de travail. Pas encore le réseau de casino, ses tapis/estrades/rideaux, ni des collisions ou transitions en jeu.**
