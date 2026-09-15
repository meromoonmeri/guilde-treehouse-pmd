# Falinks #0870 — portraits, version 2 (voie générateur d'image)

Deuxième version demandée par l'utilisateur. La version 1, dérivée directement
du portrait publié, est conservée intacte dans `portrait/0870_v1_derive/`.
Cette version 2 est livrée dans `portrait/0870_v2_generateur/`.

## Configuration du générateur

Le générateur n'est pas laissé libre. Il reçoit le portrait canonique agrandi
(`reference/normal_x512.png`) comme référence d'entrée, et une consigne qui
contraint explicitement :

- **vrai pixel art**, même résolution apparente et même taille de pixel que la
  référence, arêtes crénelées, pas d'anti-aliasing, pas de tracé vectoriel,
  pas de dégradé, palette indexée plate ;
- design canonique verrouillé : casque doré arrondi, plaque faciale anthracite,
  yeux cyan à reflet blanc, crête rouge dentelée, mentonnière jaune, reflet
  blanc à gauche du casque, Falinks voisins visibles sur les bords ;
- cadrage, taille de tête, angle 3/4 et découpe identiques dans les 16 cases ;
- **seuls les yeux et les petits détails d'expression changent** ;
- aucun texte, aucune bordure, aucun autre Pokémon.

Un premier essai en style vectoriel lisse a été rejeté et relancé : seule la
planche pixel art est conservée.

## Chaîne dessin → sprite → fond

1. **Dessin BIG** : `reference/big_expressions.png`, 1024 × 1024, 16 cases de
   256 × 256, une expression par case.
2. **Retour à la grille native** : chaque case est réduite par filtre BOX sur
   le pas de pixel réel de l'image générée, ce qui supprime le flou de
   rééchantillonnage du modèle.
3. **Détourage** : le ciel et le sol plats de la case sont retirés, le
   personnage est isolé par distance colorimétrique.
4. **Alignement canonique** : le personnage est remis exactement dans la boîte
   englobante du portrait publié, donc même taille de tête et même position que
   l'entrée SpriteCollab.
5. **Verrouillage du style** : chaque pixel du personnage est ramené aux
   **12 couleurs exactes** du portrait publié. Aucune teinte inventée par le
   générateur ne survit.
6. **Fond canonique** : composition sur la case correspondante de
   `portrait/0186/template.png`, sans redimensionnement.

Les quatre slots `Special` réutilisent une étude dont l'humeur colle au
personnage : salut discipliné, assurance, repos, cri de guerre.

## Contrôle

```bash
python source/portraits_falinks_v2/build_portraits.py
python source/portraits_falinks_v2/verify_portraits.py
```

## Réserve honnête

La v2 redessine aussi `Normal`, elle ne conserve donc pas les pixels amont de
SpriteCollab, contrairement à la v1. Les contrôles portent sur le format,
la palette, les miroirs et les fonds, pas sur une validation en jeu ni sur une
approbation SpriteCollab.
