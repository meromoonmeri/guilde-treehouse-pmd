# Galerie générée — traitement selon la méthode du kit d’origine

**Premier module traité. Les huit autres couloirs/paliers ne sont pas encore remplacés.**

[Ouvrir l’aperçu avec les calques](apercu.html)

## Même chaîne de travail, avec le générateur actuel

La méthode a été vérifiée dans `source/rebuild_kit.py` à la révision `6c4ac5a` et dans l’audit du dépôt :

1. **Générer l’image maîtresse aplatie**, en utilisant les natifs de la guilde comme références de DA.
2. Conserver la sortie brute, puis préparer un **natif indexé sur fond magenta**.
3. Détourer et **extraire les calques après génération** : sélection de régions, segmentation du sol, structure, bordure et éléments distincts.
4. Isoler une partie des ombres déjà présentes, avec compensation sous-jacente pour que leur recomposition retrouve l’image générée. **Aucune ombre ni texture de mur n’est dessinée par script.**
5. Produire la nuit par transformation de palette, sans régénérer une autre géométrie.
6. Exporter PNG, Aseprite et Tiled sur une **grille de 8 px**, puis relire/recomposer les fichiers.

Les anciens prompts, le modèle et ses paramètres n’étant pas archivés, ce sont les étapes vérifiables qui sont reprises — pas des réglages originaux supposés.

## Ce module

- **648 × 432 px**, comme les petits intérieurs du kit initial.
- Source : `source/hallways/generations/galerie_est_ouest_retenue.png`, réellement produite par l’outil de génération d’images.
- Natif préparé : `source/hallways/generations/natifs/galerie_est_ouest.png`, 255 couleurs de dessin et une entrée magenta réservée.
- **11 emplacements de calques, dont 5 non vides** : sol, murs, végétation haute, ombres extraites, bordure avant.
- Aucun paysage, cadre de fenêtre, tableau, porte ou objet inventé pour remplir les cases restantes. Aucun éclairage supplémentaire peint par code.
- Versions jour/nuit fixes. La recomposition de jour retrouve exactement le natif détouré préparé.

Le natif a été ramené au format de travail par voisin le plus proche et palette réduite. Il ne faut pas confondre cette préparation avec une conservation de chaque pixel de la sortie brute haute résolution.

## Fichiers

- `base_jour_transparente.png`, `base_nuit_transparente.png` : compositions RGBA.
- `base_jour_magenta.png`, `base_nuit_magenta.png` : contrôle du détourage.
- `calques/jour/` et `calques/nuit/` : les 11 PNG séparés.
- `galerie_jour.aseprite`, `galerie_nuit.aseprite` : une image fixe, les 11 calques, grille 8 px.
- `galerie_jour.tmj`, `galerie_nuit.tmj` : reconstitution des mêmes calques dans Tiled.
- `kit.json`, `controle_qualite.json`, `controle_navigateur.json` : métadonnées et résultats des contrôles.

## Limites, comme pour un découpage d’image aplatie

Les calques ne sortent pas nativement du générateur. Masquer la végétation peut laisser une zone transparente : la surface cachée derrière elle n’a pas été inventée. Une partie de l’ambiance et des ombres reste intégrée aux textures. Les tuiles Tiled recomposent les images ; elles ne constituent pas un système d’autotiles de construction universel.

## Reconstruire

Depuis la racine du dépôt :

```bash
python source/hallways/generations/exporter_methode_origine.py
python source/hallways/generations/verifier_methode_origine.py
```

Pour préparer à nouveau le natif et ses masques à partir de la génération brute, ajouter `--preparer` au constructeur. Les masques sont figés entre deux préparations afin de rendre les exports stables.

Pour vérifier aussi l’aperçu :

```bash
python source/hallways/generations/verifier_methode_origine.py --navigateur
```

Le navigateur peut être fourni via `PMD_CHROMIUM`. Les formats Aseprite/Tiled sont contrôlés par code, pas par ouverture manuelle dans leurs interfaces.
