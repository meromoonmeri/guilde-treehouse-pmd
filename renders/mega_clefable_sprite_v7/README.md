# Méga-Mélodelfe V7 — design validé, vol, attaque à paillettes, présentation façon SpriteCollab (lot `mega_clefable_sprite_v7`)

**Aperçu façon SpriteCollab** : ouvrir `index.html` (tuiles GIF Idle, Walk, Sleep, Hurt, Attack, Charge, Dance, Withdraw, Swing, Double, Rotate, Hop — direction face, comme sur sprites.pmdcollab.org — puis version 8 directions). GIF individuels : `anim_<Anim>.gif` et `anim_<Anim>_8dir.gif`.

## Ce qui change
- **Walk / Idle (et Hop, Dance, Withdraw, Rotate)** : vrai cycle de vol dessiné par le générateur (ailes déployées → repliées haut → déployées → basses, corps qui monte/descend, pieds ballants), face / profil / dos, sur les trajectoires canoniques CHUNSOFT.
- **Attack / Strike / Swing / Double / Charge** : le personnage reste en place et **des paillettes apparaissent, culminent en anneau autour d'elle, puis disparaissent** (bandes générées face / profil / dos ; phase répartie sur le nombre de frames canonique de chaque animation).
- Hurt / Sleep : poses V6 conservées (design cohérent).
- Design : image validée par l'utilisateur ; carte de design réutilisée pour toutes les bandes.

## Audit de détail (`source/mega_clefable_sprite_v7/audit_details.json`)
Pour les 12 animations : toutes les cases d'une même feuille ont **la même taille** ; **yeux bleus visibles dans 100 % des cases où le visage est visible** (les yeux sont re-tamponnés en style canonique de la référence utilisateur : point bleu vif 2×2 (0,162,232), sans paupière sombre) ; **ailes présentes dans 100 % des cases** ; **calotte blanche dans 100 % des cases** ; **0 tache sombre sur les mains** (contrôle des blobs sombres bas du corps). Hauteur du corps 34 px stable (34–35 sur les attaques ; 34–43 sur les cycles de vol = ailes repliées vers le haut, voulu). Les bandes ¾ dont l'audit avait révélé des défauts (yeux absents sur 3 frames, calotte perdue) ont été écartées : les directions ¾ utilisent la vue de face.
`verify.py` 64/64 PASS (format PMDOWiki, Offsets/Shadow canoniques après retrait du padding, ≤16 couleurs, alpha binaire…).

## Fichiers
`sprite/0036/0001/` (13 anims, AnimData.xml, credits.txt), `0036_0001_mega_clefable_v7_spritecollab.zip`, `index.html` + 24 GIF, `planche_<Anim>.png`, `manifest.json` (SHA256 des bandes).
Limites : art IA déclaré ; ¾ = vue de face ; ¾ dos = vue de dos ; non testé en moteur ; V1–V6 conservés.
