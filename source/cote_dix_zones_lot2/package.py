"""Publish the independent lot-2 preview and native pack; never rewrite lot 1."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    template=(ROOT/'source/cote_dix_zones/viewer.html').read_text()
    replacements={
        'Côtes Métano · 10 nouvelles zones':'Côtes Métano · lot 2 · zones 11 à 20',
        'Dix nouveaux horizons':'Dix nouveaux horizons — lot 2',
        '10 nouveaux lieux + 2 côtes V2 · 24 Ground':'Zones 11 à 20 · 10 lieux · 20 Ground',
        'cote_metano_dix_zones_pmdo.zip':'cote_metano_dix_zones_lot2_pmdo.zip',
        'Les deux terrains V2 restent les visuels générés précédents.':'Ce lot ne remplace aucune carte du premier lot.',
        "'dix_zones_'":"'dix_zones_lot2_'",
    }
    for old,new in replacements.items():template=template.replace(old,new)
    (HERE/'viewer.html').write_text(template)
    spec=importlib.util.spec_from_file_location('shared_coasts_package',ROOT/'source/cote_dix_zones/package.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    p.HERE=HERE;p.WEB=ROOT/'sprites/cote_dix_zones_lot2'
    p.PACK=Path.home()/'.cache/cote_dix_pack_lot2'
    p.VIEWER_NAME='apercu_dix_zones_metano_lot2.html'
    p.ZIP_NAME='cote_metano_dix_zones_lot2_pmdo.zip';p.EXPECTED_TOTAL=20
    p.main()


if __name__=='__main__':main()
