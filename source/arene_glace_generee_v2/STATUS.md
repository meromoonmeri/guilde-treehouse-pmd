# Correction de méthode utilisateur

« tu dois faire la méthode que tu avais fais dans render genere pas des bouts de map etc ».

Retour au pipeline `renders/layouts_magenta_v1` et au terrain Northern sur magenta. Deux générations : décor complet, puis sol complet nettoyé sous les reliefs. Terrain final issu de cette composition unique, **pas une reconstruction par collage de maps**. Normalisation et détourage, masques de plans, ORA, animationBG séparée et galerie interactive.

L’ancien terrain d’arène en morceaux de maps est remplacé pour cette demande, mais conservé historiquement. Les aurores/étoiles animées précédentes sont réutilisées sans modification ; leur animation reste explicitement une création nouvelle sur le dessin canonique. Ne pas qualifier les matériaux du nouveau terrain généré de pixels canoniques certifiés.

Source de build : `source/arene_glace_generee_v2/build.py`. Résultat : `renders/arene_glace_generee_v2/`. Reproduction : lancer build.py puis package.py, qui exécute les11tests dédiés avant ZIP/rapport. PNG, masques, ORA, GIF/WebP et aperçu à cases de calques ; aucun runtime PMDO validé.
