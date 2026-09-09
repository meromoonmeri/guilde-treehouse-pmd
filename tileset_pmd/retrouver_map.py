from __future__ import annotations

"""Cherche toutes les copies recuperables d'une carte PMDO sur ce PC.

A lancer SUR TA MACHINE (celle ou tourne PMDO), pas dans le depot :

    python3 retrouver_map.py TEST120

Le script ne modifie ni ne supprime rien. Il ne fait que lire et lister.

Il cherche, par ordre d'interet :
  1. le .rsground dans les emplacements ou PMDO ecrit (Data/Ground, MODS/*/Data/Ground)
  2. les .jsonpatch : si la carte a ete chargee comme diff, PMDO sauvegarde
     dans TEST120.jsonpatch et SUPPRIME le .rsground (DataManager.SaveObject)
  3. les copies temporaires / de synchro laissees par l'OS ou le cloud
  4. les dossiers de scripts Data/Script/.../ground/<nom>/ : leur presence
     prouve qu'un DoSave complet a eu lieu, donc qu'une carte a bien existe
  5. les logs LOG/*.txt : ils tracent chaque chargement de carte et permettent
     de dater la derniere fois ou la carte s'est chargee correctement
"""

from pathlib import Path
import sys
import os
import json

# Un vrai .rsground fait au minimum quelques dizaines de Ko.
# Les cartes de reference (Halcyon) vont de 180 Ko a 40 Mo.
SUSPECT_MAX = 64          # <= 64 octets : vide ou quasi vide (un BOM fait 3 octets)
PLAUSIBLE_MIN = 20_000    # au-dela : contenu credible


def human(n: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.0f} To"


def looks_like_map(path: Path) -> tuple[bool, str]:
    """Ouvre le fichier et dit s'il contient vraiment une carte."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, f"illisible ({exc})"
    if size <= SUSPECT_MAX:
        head = path.read_bytes()[:8]
        if head[:3] == b"\xef\xbb\xbf" and size == 3:
            return False, "VIDE - uniquement un BOM UTF-8, aucun contenu"
        return False, f"VIDE ou tronque ({human(size)})"
    try:
        text = path.read_text(encoding="utf-8-sig", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"illisible ({exc})"
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        # JSON coupe net = vraie troncature, souvent partiellement recuperable
        return False, f"JSON INCOMPLET (troncature reelle) a la position {exc.pos}"
    obj = doc.get("Object", doc)
    layers = obj.get("Layers")
    if not isinstance(layers, list) or not layers:
        return False, "JSON valide mais sans calques"
    try:
        w = len(layers[0]["Tiles"])
        h = len(layers[0]["Tiles"][0])
    except (KeyError, IndexError, TypeError):
        return True, f"carte lisible ({human(size)}), calques: {len(layers)}"
    return True, f"CARTE VALIDE - {w}x{h} cellules, {len(layers)} calques, {human(size)}"


def search_roots() -> list[Path]:
    """Emplacements probables, tous OS confondus."""
    home = Path.home()
    roots = [
        home,
        home / "Documents",
        home / "Desktop",
        home / "Bureau",
        home / "Downloads",
        home / "Téléchargements",
        home / "AppData" / "Roaming",
        home / "AppData" / "Local",
        home / "Library" / "Application Support",
        home / ".local" / "share",
        home / "OneDrive",
        home / "Google Drive",
        home / "Dropbox",
        Path("C:/") if os.name == "nt" else Path("/"),
    ]
    seen, out = set(), []
    for r in roots:
        try:
            if r.is_dir() and r not in seen:
                seen.add(r)
                out.append(r)
        except OSError:
            pass
    return out


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "TEST120"
    print(f"Recherche de la carte '{name}' sur ce PC.")
    print("Aucun fichier ne sera modifie ni supprime.\n")

    patterns = [
        f"{name}.rsground",
        f"{name}.jsonpatch",
        f"{name}.rsground.tmp",
        f"{name}.rsground.bak",
        f"{name}*.rsground*",
    ]

    found: dict[Path, tuple[bool, str]] = {}
    script_dirs: set[Path] = set()
    logs: set[Path] = set()
    other_maps: set[Path] = set()
    visited: set[str] = set()

    for root in search_roots():
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda e: None):
            # On evite de fouiller des arborescences inutiles et enormes.
            dirnames[:] = [
                d for d in dirnames
                if d not in {"node_modules", ".git", "Windows", "$Recycle.Bin",
                             "Program Files", "Program Files (x86)", "proc", "sys", "dev"}
            ]
            # Les racines se chevauchent (ex: / et /home/toi) : on ne visite
            # chaque dossier reel qu'une seule fois.
            try:
                key = os.path.realpath(dirpath)
            except OSError:
                key = dirpath
            if key in visited:
                dirnames[:] = []
                continue
            visited.add(key)

            here = Path(dirpath)
            low = here.name.lower()

            if low == name.lower() and "ground" in dirpath.lower().replace("\\", "/"):
                script_dirs.add(here)

            for fn in filenames:
                p = here / fn
                fl = fn.lower()
                nl = name.lower()
                # Tout fichier dont le nom commence par celui de la carte est
                # candidat : .rsground, .jsonpatch, .tmp, .bak, copies cloud...
                if fl.startswith(nl) and (
                    ".rsground" in fl or fl.endswith(".jsonpatch")
                ):
                    found[p] = looks_like_map(p)
                elif fl.endswith(".rsground"):
                    other_maps.add(p)
                elif fl.endswith(".txt") and "log" in dirpath.lower():
                    logs.add(p)

    print("=" * 70)
    print(f"1. FICHIERS '{name}' TROUVES")
    print("=" * 70)
    if not found:
        print("  Aucun. La carte n'est pas sous ce nom sur ce PC.")
    recoverable = []

    def size_of(p: Path) -> int:
        try:
            return p.stat().st_size
        except OSError:
            return 0

    for p in sorted(found, key=size_of, reverse=True):
        ok, why = found[p]
        mark = "[OK]  " if ok else "[VIDE]"
        print(f"  {mark} {p}\n         -> {why}")
        if ok:
            recoverable.append(p)

    print()
    print("=" * 70)
    print("2. DOSSIERS DE SCRIPTS ASSOCIES")
    print("=" * 70)
    if script_dirs:
        print("  Leur presence prouve qu'une sauvegarde complete a eu lieu :")
        for d in sorted(script_dirs):
            print(f"  - {d}")
    else:
        print("  Aucun dossier de script a ce nom.")

    print()
    print("=" * 70)
    print("3. AUTRES CARTES PRESENTES (pour localiser ton dossier de mod)")
    print("=" * 70)
    if other_maps:
        for p in sorted(other_maps)[:25]:
            try:
                print(f"  {human(p.stat().st_size):>8}  {p}")
            except OSError:
                pass
        if len(other_maps) > 25:
            print(f"  ... et {len(other_maps) - 25} autres")
    else:
        print("  Aucune autre carte trouvee.")

    print()
    print("=" * 70)
    print("4. LOGS PMDO (tracent chaque chargement de carte)")
    print("=" * 70)
    hits = []
    for lg in sorted(logs)[:200]:
        try:
            txt = lg.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if name.lower() in txt.lower():
            for line in txt.splitlines():
                if name.lower() in line.lower() and (
                    "rsground" in line.lower() or "Completed" in line
                ):
                    hits.append((lg, line.strip()))
    if hits:
        print("  Mentions de la carte dans les logs :")
        for lg, line in hits[-15:]:
            print(f"  [{lg.name}] {line}")
        print()
        print("  Une ligne 'Completed file load.' apres 'Loading rsground file:"
              f" {name}' prouve que la carte s'est deja chargee correctement.")
    else:
        print("  Aucune mention dans les logs trouves.")

    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    if recoverable:
        print("  Ta carte est RECUPERABLE. Copie la plus grosse de ces versions :")
        for p in recoverable:
            print(f"    {p}")
    else:
        print("  Aucune copie exploitable trouvee sous ce nom.")
        print("  Etapes suivantes : corbeille, historique de fichiers / Time Machine,")
        print("  versions precedentes OneDrive/Drive/Dropbox, et le point 3 ci-dessus")
        print("  pour verifier que tu cherches dans le bon dossier de mod.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
