couloir_t: DEFERRED — 2 generations (v2 stem touched S edge, v3 came out full-bleed cross).
v3 reassigned as salle_carrefour (4 grass openings verified). Gap cross kept as carrefour_clairiere
(gaps ~21px @512, bridged by native connector strip, covered by opaque-band test).
Next turn (image limit resets): generate 1 true T (N/E/W, bottom closed) -> 7th piece.
Generation log: 6 initial + 3 retries + 1 T-retry = 10/10 this turn.

## V3 — multicalque sol/chemin/arbres/rochers/bordure jungle (24 septembre 2026)
7 bordures régénérées style Southern Jungle (lianes, grosses feuilles), réf
Southern_Jungle_entrance_S.png + brut de chaque pièce, fenêtres aux accès.
Anciennes bordures jardin conservées dans renders/.../bordures/ (archives).
Terrains inchangés. Nouveau schéma : 01_sol (rives), 02_chemin (bande centrale
géométrique, érosion 15px), 03_arbres (cimes claires + troncs, toutes profondeurs),
04_buissons (verts sombres), 05_rochers, 06_fleurs (+4 phases), 07_bordure_jungle,
08_acces. V2 (fond/cimes/premier plan/troncs séparés) dans l'historique git.

## V4 — layouts séparés sol/chemin/fleurs/rochers (24 septembre 2026, 2 zones)
Passage progressif : chaque élément généré seul sur magenta (mêmes noms de couches).
Ce tour (10/10) : couloir_ns + salle_carrefour (4+4), +reprise chemin carrefour
(était beige dirt -> herbe), +reprise fleurs carrefour (guirlandes denses ->
bouquets clairsemés). Assemblage : chemin⊆sol, végétation V3 rognée hors nouveau
sol, rochers/fleurs⊆(sol|végétation). Bordure jungle + accès V3 inchangés.
Restent : ew, t, traversee, laterale, clairiere (20 générations).
Note sandbox : 5e réinitialisation vue sur le projet ; historique réintégré
(fetch + reset --hard sur origin ce22a6eb), stash redondant jeté, layouts
sauvegardés/restaurés depuis /tmp, .venv reconstruite.

## V5 — nues, tilesheets, végétation animée (24 septembre 2026)
Aucune génération : versions nues (sol+chemin+fleurs+accès), tilesheets rochers
(88 sprites ≥60px, masqués par composante) + buissons (127 sprites ≤128px, 4 phases),
végétation balancée 4×200ms, GIF full. Ordre d'empilement unifié (fleurs <
bordure < accès). Sandbox réinitialisée 6e fois : même réintégration, sans perte.

## V4 — suite layouts ew + t (24 septembre 2026, 8/10 ce tour + 2 falaises V3)
couloir_ew : sol (corridor E-W, encoches haut)/chemin/fleurs/rochers ; couloir_t :
vrai T (N/E/W, bas fermé)/chemin/fleurs/rochers. Guidage par ref : sol depuis
terrain V3 + sol ns ; dépendants depuis nouveau sol.
Constats : sols + rochers (isolés magenta) OK ; chemins BEIGE + formes
parasites (blobs ew, trou U t) -> A REPRENDRE en bande/tige HERBE comme ns
(log V4 : chemin = herbe, pas dirt) ; fleurs = herbe+bouquets (copie ref) ->
salvage prévu par partition couleurs V3 au build (pas de reprise).
Reste : reprises chemin ew+t + traversee/laterale/clairiere (12) = 14 générations.

## V4 — traversee + laterale + reprises chemin (24 septembre 2026, 10/10)
Reprises chemin ew (bande herbe) + t (T herbe) OK. Sols v1 traversee/laterale
avec ARBRES (murs d'arbres) -> repris SANS arbres (rims buissonnants) : OK
(note : 2 moignons troncs haut sol traversee, caches par bordure V3).
fleurs traversee/laterale SANS ref (texte seul) : bouquets isoles magenta OK.
Echec : chemins traversee/laterale = COPIES du sol (ref trop suivie) ->
A REPRENDRE texte seul (bande N-S / L W+S positionnes). Rochers
traversee/laterale reportes. Fleurs ew/t : salvage partition couleurs V3.
Reste : clairiere(4) + rochers trav/lat(2) + chemins trav/lat(2) = 8 generations.

## V4 — 7/7 : clairiere + integrations (24 septembre 2026, 10/10)
Clairiere : sol 4-voies (N/S/E/W + rond central) OK ; chemin CROIX texte seul
OK ; fleurs texte seul (~90% magenta, ~16 bouquets) OK ; rochers = copie sol.
Chemin traversee retry texte seul : bande N-S OK. Chemin laterale : 3 retries
texte seul ; coords pixel ignorees (#1=#2 : L haut-droit, tige rate encoche S)
-> #3 ancre semantique « centre » (barre OK, tige ~40px droite) + SHIFT
scripté (-40,0) 8px dans build_v4 (repositionnement rigide, classe V1 gravity).
Rochers salles/clairiere = copies -> partition gris scriptée (cores neutres +
outlines adjacents, trous bouchés, >60px gris). Fleurs ew/t -> partition V3
pétales + feuillage sombre voisin (V4-bouquet). Rock-rules salles neuves
uniquement (précédent ns/carrefour figé, hash vérifié) : composantes
60..15000px + jamais sur chemin dilaté 4px (pistes lisibles). Effets : sol
cobble traversee éjecté (05 vide), murs ew éjectés (05 vide), pile centrale t
dégagée. couloir_t : 04 vide (sol couvre toute V3) -> TRANSPLANT scripté de 6
buissons ns (<=64px) aux coins (ancres 8px fixes, hors-sol vérifié).
V5 régénéré (nappes vides gérées) + verify OK 7/7 + galerie V5 + 8 zips
workspace (7 SALLE + COMMUN, non committés : redondants avec renders/ suivis).
Budget falaises+jardin du tour épuisé (10/10).
