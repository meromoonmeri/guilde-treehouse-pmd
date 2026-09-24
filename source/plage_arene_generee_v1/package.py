"""Package plage V1 : relance les tests puis ecrit le ZIP."""
from pathlib import Path
import subprocess
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
O = R / "renders/plage_arene_generee_v1"
ZIP = R / "renders/plage_arene_generee_v1_pack.zip"


def main():
    r = subprocess.run([sys.executable, "-m", "unittest",
                        "source.plage_arene_generee_v1.test_build"], cwd=R)
    r.check_returncode()
    fichiers = sorted(O.rglob("*")) + [R / "apercu_plage_arene_v1.html",
                                       SRC / "build.py", SRC / "test_build.py",
                                       SRC / "package.py", SRC / "STATUS.md",
                                       SRC / "viewer.html",
                                       SRC / "generation/brut_scene.png",
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
