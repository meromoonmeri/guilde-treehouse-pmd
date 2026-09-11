# Banque commune de nuages

`nuages_six_formes.png` est la feuille générée, normalisée à 720 × 432 px et détourée : deux colonnes, trois lignes. Chaque cellule contient une famille différente, pas simplement une copie redimensionnée du même nuage.

Ordre : cumulus vertical, forme effilée, banc horizontal, cirrus, fragments isolés, forme déchiquetée. Lumière ivoire, tons bleu-poudre et ombres pervenche. Pas de ciel ni d’astre dans cette feuille.

`source/prepare_nuages.py` découpe les six cellules, réduit chaque silhouette au plus proche voisin, la place dans le ciel natif et maîtrise la palette à 96 tons. Il conserve la transparence et n’invente pas de nouvelle forme. La palette évite de stocker des milliers de couleurs presque identiques dans chaque cel animé.

Les phases d’animation ne sont pas de nouvelles images générées : les nuages sont déplacés ; les étoiles voient leur opacité varier selon la table conservée dans les manifestes ; les vagues suivent leur table de déplacement et d’intensité. Aseprite, Tiled et l’aperçu utilisent ces mêmes données.
