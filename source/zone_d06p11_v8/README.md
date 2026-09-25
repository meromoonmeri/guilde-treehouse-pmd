# Zone D06P11 V8
Dérivé V7 (composition approuvée conservée).
- Terrain : `generation/falaise_v8_nettoyee.png` = guide V7 dont le fragment rocheux flottant en haut à droite (6883 px du guide, composante déconnectée) a été retiré. Aucun autre pixel modifié. La lune se replace automatiquement dans le ciel libéré (513,39).
- Collision : marches + bouche de grotte rendues marchables (1356 cases, zone unique). Le warp vers le donjon reste à poser dans l'éditeur.
- Nouveau calque `04c_ecume` : écume **générée** (`generation/ecume_frames.png`, 8 frames, 6 f = 100 ms), 12 sites au pied des falaises gauche/droite, phases décalées, étalonnée par mode, entre la mer et le terrain.
- Textures : génération ramenée sur la palette ROM de la V2. Ce ne sont PAS des pixels ROM exacts. Seuls la mer (BPA 10 f / palette 7 f) et le ciel viennent de la ROM.
- Non testé en jeu. Construction : `.venv/bin/python source/zone_d06p11_v8/build.py`.
