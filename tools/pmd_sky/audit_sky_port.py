"""Audit d'un clone de meromoonmeri/PMD-SKY-PMDO-PORT.
Usage : python tools/pmd_sky/audit_sky_port.py /chemin/PMD-SKY-PMDO-PORT audits/pmd_sky_port
Classe chaque .rsground : code MAP_BG, famille (préfixe), taille, animation (frames/FrameLength),
collision (obstacles Tags!=0) -> JOUABLE (collision BMA) ou BG (aucune collision).
"""
import json, re, sys, csv, collections, pathlib
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
FAM = {"t": "ville (Town)", "g": "guilde (Guild)", "d": "donjon : abords/salles (Dungeon ground)", "v": "scène/cinématique (Visual)",
       "s": "spécial/histoire (Special)", "p": "lieux divers (Place)", "h": "Hidden/divers", "b": "plage/début (legacy)"}
rows = []
for p in sorted((src / "output" / "Grounds").glob("*.rsground")):
    d = json.load(open(p, encoding="utf-8-sig"))["Object"]
    m = re.search(r"MAP_BG ([a-z0-9]+)/", d.get("Comment", "")); code = m.group(1) if m else p.stem
    L = d["Layers"][0]["Tiles"] if d.get("Layers") else []; W, H = len(L), (len(L[0]) if L else 0)
    nfr, fl = collections.Counter(), collections.Counter()
    for col in L:
        for t in col:
            for lay in t.get("Layers", []):
                nfr[len(lay["Frames"])] += 1; fl[lay.get("FrameLength")] += 1
    obs = d.get("obstacles", []); blocked = sum(1 for c in obs for t in c if t.get("Tags", 0))
    mm = re.match(r"([a-z])(\d\d)p(\d\d)([a-z]?\d?)", code)
    fam = FAM.get(code[0], "?") if mm else "asset nommé"
    salle = ""
    if mm and code[0] == "d":
        pp = int(mm.group(3)); salle = {1: "entrée (p1x)", 3: "intermédiaire (p3x)", 4: "fond/boss (p4x)"}.get(pp // 10, f"p{pp}")
    frames = max(nfr) if nfr else 1
    rows.append({"fichier": p.stem, "map_bg": code, "famille": fam, "groupe": mm.group(1) + mm.group(2) if mm else "",
                 "position": salle, "variante": mm.group(4) if mm else "", "largeur_px": W * 8, "hauteur_px": H * 8,
                 "frames_anim": frames, "tuiles_animees": sum(v for k, v in nfr.items() if k > 1),
                 "frame_length": ",".join(str(k) for k in sorted(fl, key=str)), "cases_bloquees": blocked,
                 "type": "JOUABLE" if blocked else "BG (sans collision)", "nom": d["Name"]["DefaultText"]})
with open(out / "inventaire_grounds.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(out / "inventaire_grounds.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
S = collections.Counter((r["famille"], r["type"]) for r in rows)
an = [r for r in rows if r["frames_anim"] > 1]
summ = {"total": len(rows), "jouables": sum(r["type"] == "JOUABLE" for r in rows), "bg": sum(r["type"] != "JOUABLE" for r in rows),
        "animees": len(an), "frame_length_animees": dict(collections.Counter(r["frame_length"] for r in an)),
        "par_famille": {f"{a} | {b}": n for (a, b), n in sorted(S.items())},
        "top_animees": sorted(((r["map_bg"], r["frames_anim"], r["tuiles_animees"]) for r in an), key=lambda x: -x[1])[:15]}
(out / "resume.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1)); print(json.dumps(summ, ensure_ascii=False, indent=1))
