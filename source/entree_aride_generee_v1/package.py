"""Package entree aride V1 : relance les tests puis ecrit le ZIP."""
from pathlib import Path
import subprocess
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
O = R / "renders/entree_aride_generee_v1"
ZIP = R / "renders/entree_aride_generee_v1_pack.zip"


def main():
    r = subprocess.run([sys.executable, "-m", "unittest",
                        "source.entree_aride_generee_v1.test_build"], cwd=R)
    r.check_returncode()
    fichiers = sorted(O.rglob("*")) + [R / "apercu_entree_aride_v1.html",
                                       SRC / "build.py", SRC / "test_build.py",
                                       SRC / "package.py", SRC / "STATUS.md",
                                       SRC / "viewer.html",
                                       SRC / "generation/brut_relief_magenta.png",
                                       SRC / "generation/brut_sol.png",
                                       SRC / "references/reference_originale.png"]
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in fichiers:
            if p.is_file():
                z.write(p, p.relative_to(R))
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        print(f"ZIP OK : {ZIP.name} ({len(z.namelist())} fichiers)")


if __name__ == "__main__":
    main()
