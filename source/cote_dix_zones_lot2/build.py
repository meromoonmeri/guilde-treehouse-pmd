"""Lot 2: ten additional layouts, reusing the established native pipeline and DA."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONFIG=[
 ('11_anses_jumelles','Les anses jumelles',[(-120,400,16,96,500),(-216,-24,3,96,168),(840,8,3,144,176)]),
 ('12_balcon_asymetrique','Le balcon asymétrique',[(-320,240,12,144,400),(384,-64,9,96,136)]),
 ('13_chapelet','Le chapelet marin',[(-272,-88,2,96,104),(368,160,2,96,320),(928,408,2,96,568)]),
 ('14_corniches_paralleles','Les corniches parallèles',[(-448,376,23,48,600),(-192,-24,21,48,280)]),
 ('15_mesas_decalees','Les mesas décalées',[(-88,-16,5,240,144),(768,264,6,96,416)]),
 ('16_couronne','La couronne des embruns',[(-368,320,7,96,488),(944,280,7,144,464),(352,-64,4,192,120)]),
 ('17_chenal','Le chenal profond',[(-384,128,11,192,200),(928,256,9,144,328)]),
 ('18_esplanade','La grande esplanade',[(-144,360,18,96,520),(592,-88,3,48,112)]),
 ('19_eperon','L’éperon occidental',[(736,376,4,96,544),(-424,-40,10,288,176)]),
 ('20_marches_levant','Les marches du levant',[(824,400,7,96,560),(256,160,7,96,320),(-280,-80,7,96,112)]),
]


def main():
    spec=importlib.util.spec_from_file_location('shared_coasts_build',ROOT/'source/cote_dix_zones/build.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    b.OUT=Path.home()/'.cache/cote_dix_pack_lot2'
    b.WEB=ROOT/'sprites/cote_dix_zones_lot2'
    b.CONFIG=CONFIG
    b.SHEET_PREFIX='C20_';b.MAP_PREFIX='cote20_';b.INCLUDE_V2=False
    b.main()


if __name__=='__main__':main()
