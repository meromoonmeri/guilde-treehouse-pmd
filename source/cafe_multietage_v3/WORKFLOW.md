# Café V3 — méthode de référence à conserver

La V2 (agrandissement par bandes) ne répond pas à la méthode demandée. Utiliser la méthode Northern/falaises : génération guidée par images canoniques, inspection, corrections au générateur, puis détourage/calques et vérification. Ne pas remplacer cette étape par une simple extension programmée des cartes. Les images générées restent des interprétations guidées, pas des textures natives pixel-identiques garanties.

## État après correction de l’accueil
- `renders/cafe_multietage_v3/bruts/A_ss2.png` : salle souterraine appréciée explicitement par l’utilisateur. La conserver sans modification.
- `A_accueil.png` : première proposition rejetée (bordures et fenêtres).
- `A_accueil_corrige_bois_croisillons.png` : correction générée depuis la première proposition et la référence Metano. Bordure en bois sur le pourtour, fenêtres rondes encastrées avec croisillons en bois, vitres claires sans paysage montagneux collé. Proposition présentée, pas encore approuvée.

## Contraintes acquises
Pièces vides, variantes de layout légèrement plus grandes et légèrement différentes, matériaux guidés par les vrais cafés Halcyon/Spinda. Garder les accès d’origine, leur emplacement relatif, leurs ombres et lumières. Ne pas ajouter d’escaliers au centre. Sous-sols rocheux sans fenêtres extérieures. Étages en bois ; fenêtres rondes faisant partie du décor avec croisillons, pas de disques de paysage composités au script. Étage+2 : petits hublots, aucune baie vitrée.

Le fond magenta des bruts sert au futur détourage. Aucun calque V3, aucune carte native ou validation PMDO n’est encore livré. Les autres niveaux/variantes V3 restent à produire suivant cette direction, sans modifier la proposition souterraine appréciée.

## Dernière correction utilisateur — prioritaire
« faut un style de bordure similaire à la roche underground et retire les fenêtre le tapis doit être marron clair café ».
Nouvelle proposition `A_accueil_bordure_organique_sans_fenetres.png` générée depuis l’accueil précédent, le sous-sol apprécié et la référence native Metano : bordure organique épaisse en bois inspirée du relief rocheux souterrain, fenêtres supprimées, tapis café-au-lait. Cette demande remplace les fenêtres à croisillons pour l’accueil en cours. Ne pas les remettre automatiquement. Sous-sol apprécié inchangé. Nouvelle proposition à valider visuellement, pas encore découpée en calques.

## Correction suivante : POV strictement intérieur
L’utilisateur refuse la vue extérieure/coque de la salle et demande de regarder l’étage de Palika. Le vrai `guild_second_floor.rsground` de Halcyon a été téléchargé avec ses banques référencées puis reconstruit (`inspect_floor.py`, références et empreintes locales). Il montre des murs tournés vers l’intérieur, une bordure sombre et une coupure du sol au premier plan, pas une façade en troncs.
`A_accueil_interieur_palika.png` est la nouvelle génération guidée par cette référence native, l’accueil précédent et le café Metano original. Elle enlève les troncs extérieurs et la face haute de bois au premier plan, conserve des murs intérieurs, aucun hublot et le tapis café clair. Proposition présentée, non encore approuvée ; le seuil généré est simplifié et n’est pas une copie pixel-identique de son éclairage natif. La salle souterraine appréciée reste inchangée.

## Bordures et lumière avec POV intérieur conservé
Demande : garder POV/layout de `A_accueil_interieur_palika.png`, rendre les bordures en bois similaires au langage formel rocheux du sous-sol et remettre le jeu de lumière sur le tapis café clair.
Deux passes générateur effectuées. `A_accueil_interieur_bois_lumiere.png` ajoute le relief de bois mais laisse le tapis plat (intermédiaire non final). `A_accueil_interieur_bois_lumiere_corrige.png` corrige localement le seuil avec arcs crème/café-au-lait et coins supérieurs ombrés. Cette dernière est la proposition présentée. Murs intérieurs, disposition générale et absence de fenêtres conservés ; relief périphérique nouveau, pas copie canonique pixel-identique. Pas d’approbation utilisateur encore. Sous-sol apprécié inchangé.
