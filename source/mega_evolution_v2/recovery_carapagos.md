# Recherche de la première planche Carapagos — 16 septembre 2026

Vérifications effectuées sans modifier les sauvegardes :
- Recherche des noms tirtouga/car apagos/sprite_absents sous /home/user : seule V2 retrouvée.
- Historique Git de source/pokemon_custom/tirtouga_v1 et source/sprite_absents_v1 : aucun commit.
- Stash arena-safety-before-mega-resume, y compris ses fichiers non suivis : aucun de ces chemins.
- git fsck --full --no-reflogs --unreachable : aucun objet orphelin signalé.

Conclusion bornée : pas récupérable dans les fichiers et objets Git accessibles de ce checkout. Le souvenir de la génération V1 existe, mais pas son image. Ne pas annoncer une nouvelle génération comme une récupération. Ne pas appliquer le nouveau style V2 rejeté à davantage d'actions. Une copie de l'image originale provenant de l'ancien échange permettrait de repartir fidèlement de V1.
