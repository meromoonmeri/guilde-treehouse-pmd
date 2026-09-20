"""Déclarations des cartes Spriter Pro v1 — six compositions neuves (04 à 09).

Chaque carte est décrite par :
- `ribbons` : parois rocheuses canoniques (rubans de colonnes natives).
    x      : départ du ruban en px (peut être négatif, hors champ à gauche)
    offset : décalage vertical de la paroi en px (le plat supérieur est à 456+offset)
    extra  : hauteur supplémentaire de face en px (répétition de rangées natives)
    flats  : nombre de segments de front plat (blocs de 8 colonnes)
- `streams` : torrents nord -> sud (réservoir natif, chutes, chenaux).
    x     : centre de la bande en px
    walls : index des parois traversées par une chute (toutes, ordre nord -> sud)
- `lakes` : bassins isolés (rangées natives consécutives du réservoir).
    x : centre en px, top : haut en px, rows : nombre de rangées natives (1..57)

La tête des torrents répète la rangée de surface du réservoir natif : plus le
plateau nord est haut (offset), plus le réservoir est large avant de se
resserrer — comme dans les cartes de référence.

Contraintes vérifiées par engine.validate_layout avant toute pose :
alignement 8 px, chutes >= 17 rangées sur un front plat, bandes sans recouvrement,
bassins entièrement dans une plaine (aucune face coupée).
"""

LAYOUTS = [
    {
        'id': '04_lac_suspendu',
        'name': 'Le lac suspendu',
        'description': 'Un plateau nord élevé alimente une grande chute centrale ; '
                       'deux bassins canoniques isolés posés dans la plaine.',
        'ribbons': [{'x': -64, 'offset': 224, 'extra': 192, 'flats': 27}],
        'streams': [{'x': 1024, 'walls': [0]}],
        'lakes': [{'x': 512, 'top': 1104, 'rows': 24},
                  {'x': 1536, 'top': 1240, 'rows': 20}],
    },
    {
        'id': '05_double_cirque',
        'name': 'Le double cirque',
        'description': 'Deux parois superposées, deux doubles chutes parallèles et '
                       'deux bassins entre les niveaux.',
        'ribbons': [{'x': 0, 'offset': 240, 'extra': 128, 'flats': 24},
                    {'x': -192, 'offset': 760, 'extra': 128, 'flats': 28}],
        'streams': [{'x': 640, 'walls': [0, 1]},
                    {'x': 1408, 'walls': [0, 1]}],
        'lakes': [{'x': 256, 'top': 944, 'rows': 24},
                  {'x': 1792, 'top': 992, 'rows': 20}],
    },
    {
        'id': '06_deux_torrents',
        'name': 'Les deux torrents',
        'description': 'Trois niveaux en gradins ; deux torrents à triple chute '
                       'descendent toute la carte.',
        'ribbons': [{'x': -64, 'offset': 224, 'extra': 128, 'flats': 26},
                    {'x': -160, 'offset': 608, 'extra': 128, 'flats': 27},
                    {'x': -256, 'offset': 880, 'extra': 96, 'flats': 28}],
        'streams': [{'x': 512, 'walls': [0, 1, 2]},
                    {'x': 1536, 'walls': [0, 1, 2]}],
        'lakes': [],
    },
    {
        'id': '07_grande_face',
        'name': 'La grande face',
        'description': 'Une paroi de 43 rangées de face au centre de la carte, '
                       'une chute unique et deux bassins au pied.',
        'ribbons': [{'x': 0, 'offset': 296, 'extra': 256, 'flats': 24}],
        'streams': [{'x': 1024, 'walls': [0]}],
        'lakes': [{'x': 384, 'top': 1312, 'rows': 24},
                  {'x': 1664, 'top': 1312, 'rows': 24}],
    },
    {
        'id': '08_etangs_altitude',
        'name': 'Les étangs d\u2019altitude',
        'description': 'Deux étages de parois percés par deux chutes jumelles ; '
                       'deux étangs canoniques posés au-dessus des couronnes.',
        'ribbons': [{'x': -64, 'offset': 224, 'extra': 128, 'flats': 26},
                    {'x': -192, 'offset': 928, 'extra': 64, 'flats': 28}],
        'streams': [{'x': 576, 'walls': [0, 1]},
                    {'x': 1472, 'walls': [0, 1]}],
        'lakes': [{'x': 224, 'top': 96, 'rows': 28},
                  {'x': 1824, 'top': 128, 'rows': 24}],
    },
    {
        'id': '09_trois_chutes',
        'name': 'Les trois chutes',
        'description': 'Un grand palier médian franchi par trois chutes réparties ; '
                       'un lac de plateau au nord.',
        'ribbons': [{'x': 0, 'offset': 480, 'extra': 192, 'flats': 24}],
        'streams': [{'x': 384, 'walls': [0]},
                    {'x': 1152, 'walls': [0]},
                    {'x': 1728, 'walls': [0]}],
        'lakes': [{'x': 768, 'top': 320, 'rows': 32}],
    },
]

PACK = {
    'directory': 'sprites/spriter_pro_v1',
    'sheet': 'Metano_Spriter_Pro_8px',
    'title': 'Spriter Pro v1 — six cartes canoniques',
}
