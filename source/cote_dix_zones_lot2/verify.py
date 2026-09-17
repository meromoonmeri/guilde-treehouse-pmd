"""Same independent binary/source-pixel checks, with lot-2 counts and namespaces."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    spec=importlib.util.spec_from_file_location('shared_coasts_checks',ROOT/'source/cote_dix_zones/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    v.PACK=Path.home()/'.cache/cote_dix_pack_lot2'
    v.WEB=ROOT/'sprites/cote_dix_zones_lot2'
    v.REPORT_DIR=HERE;v.EXPECTED_TOTAL=20;v.PREFIX='C20_'
    v.COMPARE_PREVIOUS=ROOT/'sprites/cote_dix_zones'
    v.main()


if __name__=='__main__':main()
