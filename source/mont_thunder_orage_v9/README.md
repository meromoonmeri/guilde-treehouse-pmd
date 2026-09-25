# Mont Thunder V9 — ciel, nuages fins et brume régénérés, calques harmonisés

Trois nouveaux guides générés, avec la scène V8 comme référence de couleurs : `ciel_guide.png`, `brume_guide.png`, `volutes_guide.png`.

- **Palette commune** : les 16 couleurs du terrain + 16 teintes tirées ensemble du ciel, des nuages, de la brume et des volutes, soit 29 couleurs au total. Tous les calques générés sont ramenés sur cette palette (0 couleur hors palette).
- **Ciel** (`00_ciel`) : les bandes du guide, lignes par ligne. Il est agrandi de 32 px ; le terrain est descendu d'autant, canevas 304×488.
- **Nuages fins** (`01_nuages_fins`) : traînées fines extraites du guide du ciel (écart à la bande). Elles restent intactes mais sont rapprochées verticalement dans la zone de ciel visible. Dérive −3 px/s, RepeatX.
- **Brume** (`02_brume_statique`) : opaque et immobile.
- **Volutes** (`03_volutes`) : 6 volutes générées qui oscillent lentement dans les vides latéraux. Elles s'éclaircissent d'1 à 3 pas pendant les impacts, synchronisées sur la timeline des éclairs (62 frames × 150 ms = 9,3 s, boucle exacte).
- **Éclairs bleus et terrain** : repris de la V8 sans changement. Le ressac animé de la V8 est retiré (brume statique demandée).
- **Limites** : ciel, brume et volutes générés, pas canoniques ; rien n'a été testé en jeu.
