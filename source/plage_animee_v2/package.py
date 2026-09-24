"""Package plage animee V2 : relance les tests puis ecrit le ZIP."""
from pathlib import Path
import subprocess
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
O = R / "renders/plage_animee_v2"
ZIP = R / "renders/plage_animee_v2_pack.zip"


def main():
    r = subprocess.run([sys.executable, "-m", "unittest",
                        "source.plage_animee_v2.test_build"], cwd=R)
    r.check_returncode()
    fichiers = sorted(O.rglob("*")) + [R / "apercu_plage_animee_v2.html",
                                       SRC / "build.py", SRC / "test_build.py",
                                       SRC / "package.py", SRC / "STATUS.md",
                                       SRC / "viewer.html",
                                       SRC / "generation/brut_mer.png",
                                       SRC / "generation/brut_sable.png",
                                       SRC / "generation/brut_roche.png"]
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in fichiers:
            if p.is_file():
                z.write(p, p.relative_to(R))
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        print(f"ZIP OK : {ZIP.name} ({len(z.namelist())} fichiers)")


if __name__ == "__main__":
    main()
