# Correction utilisateur prioritaire

Demande : finir le programme et corriger les layouts forêt/passages, qui doivent mener du sud à une grotte au nord, avec textures canoniques et calques sol/chemin/arbres/parois/entrée. Les simples agrandissements horizontaux ne répondent PAS à ce besoin.

V3 remplace les deux candidats horizontaux pour cette demande. Les autres tâches ne sont pas déclarées terminées. Galerie `apercu_entrees_sud_nord_v3.html`, exports/README/registre complet dans `exports/zones_south_north_v3/`.

Compléments natifs explicités : arbres entiers Vast Steppe pour la forêt ; vrai portail OUVERT et vrais retours de la référence underground pour le passage bleu, dont la référence seule n’a pas de grotte. Pas de masquage de ces changements de source ni de recoloration. Le candidat bleu final512×408 garde les retours natifs cohérents ; la tentative512×640 avec parois recoupées créait des raccords artificiels et a été remplacée AVANT livraison. Le premier sol quadrillé et le rectangle de fond des buissons ont aussi été corrigés avant livraison. Ne pas rétablir ces essais.

Récupération du workspace de cette relance : checkout revenu à6c4ac5a avec anciens fichiers de maps. Travail ancien sauvegardé en stash nommé, puis avance rapide àFETCH_HEAD438b9288 ; aucun original supprimé, pas de reset ou de stash pop. Branche de session inchangée.

Reproduction : `.venv/bin/python source/zones_south_north_v3/build.py` puis `.venv/bin/python source/zones_south_north_v3/package.py`. Ce dernier lance les12tests dédiés avant rapport/registre/ZIP. Le registre conserve explicitement `all_user_work_finished=false` tant que les autres tâches ne sont pas produites.
