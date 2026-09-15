# Antre V5 — eau discrète, écumes raccordées, rives suivies

Révision de détail de V4, sans nouvelle génération des parois ou de la plateforme. Les anciens livrables restent inchangés.

## Corrections
### Bassin plus subtil, dans la palette Métano/Altere
Le fond retrouve le bleu natif **RGB 131,218,230**. Les quatre poses de rides générées en V4 sont conservées mais leur contraste est ramené à 12 % de l’écart initial, avec un écart final limité à −12/+10 par canal. Les rides ne se déplacent plus visuellement par grandes différences de teinte. Leur modulation est supprimée à moins de 3 px du sec pour ne pas faire scintiller les contacts.

La variation RGB moyenne entre poses successives sur l’eau passe de 1,462 à 0,111 (sur une échelle 0–255), soit environ 92 % de réduction. Cette mesure concerne le bassin seul, pas les cascades ni les écumes. Le bassin reste une adaptation artistique de poses générées, **pas un nouvel extrait animé natif**.

### Écumes attachées au layout
Les trois poses natives Métano déjà adaptées à la taille des chutes sont maintenant ajustées à chaque poche d’eau : leurs rangées sont comprimées/décalées selon les contours réels de la rive, plutôt que simplement coupées contre les piliers. La déformation géométrique est fixe entre poses pour éviter que toute la nappe ne saute de place.

Un petit cœur d’impact persistant relie la chute à la nappe d’écume. Les composantes blanches qui ne rejoignent pas ce contact sont retirées. Chaque composante visible d’écume touche effectivement sa cascade dans chacun des 24 états. Cela corrige les fragments détachés et les terminaisons coupées constatés près des piliers.

**Ce détourage ajusté et le cœur d’impact sont des adaptations au layout**, pas des pixels natifs intacts. Les trois poses et leur cadence restent celles de la référence.

### Roche et rives
Un nouveau calque `09_rives_roche_eau` suit les contours du massif sur une bande de **3 px, uniquement côté eau** : contact bleu-gris très léger, puis petits reflets discontinus. Alpha maximal 32/255 ; pas de ligne blanche uniforme autour du bassin. Les pixels rocheux ne sont pas repeints.

Les reflets natifs autour du disque et des pas japonais restent séparés, à leur échelle d’origine, et ne sont pas remplacés par ce nouveau liseré.

## Conservé exactement
- Les quatre calques de parois/bordures Crooked de V3/V4.
- Le disque natif de 72 × 53 px et les trois pas japonais, immobiles.
- Le cycle natif de 8 poses de leurs rides/reflets, recomposable exactement avec les pierres.
- Les quatre poses de cascades adaptées en V4, leurs ouvertures et leurs positions.
- Cadence de 10 frames de jeu par pose ; cycles bassin/cascades/rives 4, écume 3, reflets des pierres 8 ; boucle commune **24 poses / 4 secondes**.

## 26 calques — 480 × 312
8 statiques et 18 animés. Les noms des PNG de scène commencent par **`raccord5_`** afin de ne pas écraser les fichiers V4 lors d’un import par basename. La composition et la planche de contrôle sont des aperçus, pas des tilesets à importer comme calques.

- `../../apercu_antre_raccords_v5.html` : aperçu autonome animé, chaque calque sélectionnable.
- `antre/COMPOSITION.png` et `antre/ANIMATION.webp` : rendu initial et boucle.
- `antre/antre_raccords_v5.ora` : 26 calques, état initial.
- `antre/raccord5_*.png` : calques plein cadre et 24 compositions.
- `CONTROLE_QUATRE_ETATS.png` : contrôle visuel des états 0, 5, 11 et 23.
- `audit.json` : mesures et résultats des contrôles supplémentaires.
- `antre_raccords_v5.zip` : paquet avec scripts et dépendances de reconstruction.

## Vérifications de détail
Le vérificateur teste les 24 recompositions opaques et le retour des cycles 4/3/8 ; les PNG/ORA ; la conservation des murs et des pierres ; la recomposition exacte des huit poses natives autour des pierres ; l’absence d’effets sur le sec ; le chevauchement chute/écume à chaque phase ; l’attache de toutes les composantes d’écume ; le liseré limité au côté eau dans sa bande de 3 px ; la stabilité de la teinte du bassin près des rives ; la diminution mesurée des variations d’animation.

Plusieurs états, dont le dernier, ont aussi été inspectés visuellement. Ces contrôles ciblés ne signifient pas que chaque défaut artistique possible est exclu. **Pas de test de rendu, de collisions ou de combat dans PMDO.** L’eau n’est pas une simulation de fluides.

Les références natives et leurs droits restent ceux décrits dans V4 : Altere Pond, Halcyon commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51`, atlas Métano archivé localement. Les deux bruts générés de V4 sont réutilisés, pas régénérés pour V5.

Depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/antre_raccords_v5/build.py
.venv/bin/python source/antre_raccords_v5/verify.py
.venv/bin/python source/antre_raccords_v5/package.py
```
