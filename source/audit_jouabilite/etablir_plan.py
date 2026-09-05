"""Plan canonique INTERNE de la guilde ; schéma et contrats, pas de décor peint."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, label

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "plans/guilde_4_niveaux"
KIT = json.loads((ROOT / "kit.json").read_text())
BY = {r["id"]: r for r in KIT["salles"]}
MEASURES = json.loads((OUT / "mesures_assets.json").read_text())
PROBES = {(r["id"], p["id"]): p for r in MEASURES["salles"] for p in r["acces"]}
LEVELS = {3: ["01", "06", "11"], 2: ["02", "12", "07"], 1: ["03", "04", "05"], 0: ["08", "09", "10"]}
SHAPES = {
    "01": ("ovale_court", "Accueil en ovale court, deux accès dans l’axe", 1.55, "Conserver les courbes et la silhouette accueillante."),
    "02": ("ovale_tres_large", "Grand ovale horizontal à baies arrondies", 3.1, "Conserver le grand hall identifiable et ses équipements encastrés."),
    "03": ("ovale_irregulier", "Grand ovale souple, élargi aux accès latéraux", 2.2, "Élargir les raccords sans produire de T anguleux ni de pans coupés."),
    "04": ("ovale_allonge", "Ovale allongé pour la grande table", 2.65, "Préserver une circulation périphérique ; pas de rectangle de cantine."),
    "05": ("ovale_alcove_douce", "Petit ovale avec une alcôve courbe", 1.55, "Aucune pièce en L ; une niche douce suffit à personnaliser la chambre."),
    "06": ("quasi_rond", "Petite chambre quasi ronde", 1.1, "Rendre le poste compact et distinct du vestibule."),
    "07": ("ovale_asymetrique", "Ovale asymétrique, comme un galet", 1.7, "Ne plus reprendre le miroir exact de 05."),
    "08": ("ovale_lobes_doux", "Ovale large à trois petites niches courbes", 2.2, "Trois couchages identifiables sans cloisonner le chemin central."),
    "09": ("ovale_evase", "Ovale évasé au sud, entrée nord resserrée", 1.45, "Quatre couchages autour d’un passage central libre."),
    "10": ("ovale_profond", "Ovale profond nord-sud", 1.05, "Différencier 10 de 08 par la profondeur, pas par un simple miroir."),
    "11": ("ovale_compact", "Ovale compact, renflement arrondi vers la vue", 1.3, "Ne plus dupliquer exactement 07 ; aucune pointe polygonale."),
    "12": ("ovale_autour_tronc", "Bureau arrondi autour du tronc", 1.75, "Le tronc reste architectural ; aucune sortie ni échelle nord ajoutée."),
}
RECTS = {
    "01": [435,130,270,145], "06": [105,150,250,150], "11": [945,380,220,165],
    "02": [380,215,775,205], "12": [900,25,240,135], "07": [225,30,250,145],
    "03": [440,150,475,195], "04": [20,170,245,155], "05": [215,440,255,140],
    "08": [30,165,310,175], "09": [530,425,315,160], "10": [955,155,220,195],
}

def safe_arrival(room, passage, canonical_rect):
    floor = np.array(Image.open(ROOT / room["source_masque"])) == 1
    eroded = binary_erosion(floor, structure=np.ones((24,24), bool), border_value=1)
    labs, _ = label(eroded)
    counts = np.bincount(labs.ravel()); counts[0] = 0
    core = labs == int(counts.argmax())
    x, y = passage["point_sol"]
    d = passage["orientation"]
    tx, ty = {"N": (x,y+24), "S": (x,y-24), "E": (x-24,y), "O": (x+24,y)}[d]
    yy, xx = np.where(core)
    # Rester hors du rectangle de transition connu pour ne pas reboucler.
    rx, ry, rw, rh = canonical_rect
    ok = ~((xx >= rx) & (xx < rx+rw) & (yy >= ry) & (yy < ry+rh))
    xx, yy = xx[ok], yy[ok]
    k = np.argmin((xx-tx)**2+(yy-ty)**2)
    return [int(xx[k]), int(yy[k])]


def room_node(rid, level):
    r = BY[rid]
    kind, name, ratio, brief = SHAPES[rid]
    ports = {}
    for p in r["passages_pmd"]:
        pid = p["id"]
        typ = "echelle_montante" if p["type"] == "echelle" else ("porte" if p["type"] == "porte_fermee" else "passage")
        pos = {"N":[.5,0],"S":[.5,1],"O":[0,.5],"E":[1,.5]}[p["orientation"]]
        if pid == "porte_maitre": pos = [1057/1280, 0]
        measure = PROBES[(rid, pid)]["gabarits"]["24"]
        adjusted = p["point_sol"] if measure["relie_au_sol_principal"] else (measure["alternative_dans_rectangle"] or p["point_sol"])
        rect = list(p["zone_transition"])
        rx, ry, rw, rh = rect
        if not (rx <= adjusted[0] < rx+rw and ry <= adjusted[1] < ry+rh):
            # Les anciens rectangles étaient des repères, pas des triggers installés.
            # Les centrer sur le vrai point de pieds évite une interaction hors sol.
            w, h = r["dimensions"]
            rect = [max(0,min(w-rw,adjusted[0]-rw//2)),max(0,min(h-rh,adjusted[1]-rh//2)),rw,rh]
        ports[pid] = {"orientation":p["orientation"], "type":typ, "position_schema":pos,
                      "repere_asset_px":p["point_sol"], "repere_canonique_px":adjusted,
                      "recalage_sans_redessiner":adjusted != p["point_sol"], "rectangle_reference_px":p["zone_transition"],
                      "rectangle_canonique_px":rect, "rectangle_recale":rect != p["zone_transition"],
                      "arrivee_reference_px":safe_arrival(r,p,rect), "declenchement":"action" if typ != "passage" else "franchissement"}
    return {"id":rid, "nom":r["nom"], "type":"piece", "niveau":level, "ports":ports,
            "schema":RECTS[rid], "statut_asset":"existant_a_integrer", "source_base":r["source_base"],
            "image":r["fichiers"]["jour"]["png"], "masque_sol":r["source_masque"],
            "forme":{"style":"arrondi", "famille":kind, "description":name, "rapport_axes_cible":ratio, "brief":brief},
            "conformite_forme":"à vérifier / différencier les quasi-doublons, sans abandonner les arrondis"}


def port(orientation, typ="passage", pos=None):
    if pos is None:pos={"N":[.5,0],"S":[.5,1],"E":[1,.5],"O":[0,.5],"D":[.5,.52],"U":[.5,.23]}[orientation]
    p={"orientation":orientation,"type":typ,"position_schema":pos,"declenchement":"action" if typ!="passage" else "franchissement"}
    if typ=="tremie_descendante":
        p["profil_securite"]={"unite":"normalisee_provisoire", "forme_ouverture":"ovale", "centre_vide":[.5,.49], "rayons_vide":[.18,.13],
                              "zone_action":[.37,.71,.26,.11], "arrivee":[.5,.91], "vide_non_praticable":True,
                              "ombre_interieure":True,"epaisseur_rebord":True,"barreaux_sous_plancher":True,"masque_rebord_avant":True}
    if typ=="echelle_montante":
        p["profil_securite"]={"unite":"normalisee_provisoire", "zone_action":[.40,.27,.20,.12],"arrivee":[.5,.53],"ombre_au_pied":True}
    return p


def circulation(ident, name, level, rect, ports, shape, source=None):
    return {"id":ident,"nom":name,"type":"palier" if ident.startswith("P") else "couloir", "niveau":level,
            "schema":rect,"ports":ports,"forme":{"style":"arrondi","famille":shape,"description":"Courbes continues, aucun angle vif ni pan coupé."},
            "statut_asset":"prototype_a_adapter" if source else "a_generer", "source_candidate":source,
            "generation":"Générateur d’images puis natif, masques et exports ; pas de décor procédural."}


def build():
    nodes=[room_node(rid,z) for z,ids in LEVELS.items() for rid in ids]
    nodes.append({"id":"TERRASSE","nom":"Terrasse nord existante", "type":"exterieur", "niveau":3,"schema":[445,12,250,70],
                  "ports":{"sud":port("S")},"forme":{"style":"arrondi","famille":"exterieur"},
                  "statut_asset":"destination_historique_carte_jouable_absente", "note":"Les six panoramas ne sont pas une carte de terrasse avec collisions."})
    gallery="tilesheets/generes/galerie_est_ouest/kit.json"
    nodes += [
        circulation("P3","Palier d’accueil",3,[450,420,240,135],{"nord":port("N"),"ouest":port("O"),"est":port("E"),"descente":port("D","tremie_descendante")},"ovale_court"),
        circulation("C3O","Retour courbe du veilleur",3,[220,395,155,120],{"nord":port("N"),"est":port("E")},"coude_courbe"),
        circulation("C3E","Galerie des éclaireurs",3,[740,435,155,90],{"ouest":port("O"),"est":port("E")},"galerie_arrondie",gallery),
        circulation("P2","Palier des missions",2,[615,475,305,120],{"nord":port("N"),"descente":port("D","tremie_descendante")},"petit_ovale"),
        circulation("C2R","Retour courbe des résidents",2,[40,90,145,260],{"est_haut":port("E",pos=[1,.12]),"est_bas":port("E",pos=[1,.88])},"retour_en_boucle_courbe"),
        circulation("P1","Palier de l’aile commune",1,[550,455,255,125],{"nord":port("N"),"ouest":port("O"),"est":port("E"),"descente":port("D","tremie_descendante")},"ovale_lobes_doux"),
        circulation("C1O","Galerie de la cantine",1,[285,197,145,110],{"ouest":port("O"),"est":port("E")},"galerie_arrondie",gallery),
        circulation("C1R","Boucle de l’aile commune",1,[1000,230,150,320],{"ouest_haut":port("O",pos=[0,.10]),"ouest_bas":port("O",pos=[0,.87])},"retour_en_boucle_courbe"),
        circulation("P0","Palier des dortoirs",0,[535,125,295,195],{"montee":port("U","echelle_montante"),"ouest":port("O"),"est":port("E"),"sud":port("S")},"ovale_evase"),
    ]
    edges=[]
    def connect(ident,a,ap,b,bp,kind="passage",note=""):
        edges.append({"id":ident,"a":{"zone":a,"port":ap},"b":{"zone":b,"port":bp},"type":kind,"bidirectionnel":True,"note":note})
    connect("EXT_N","TERRASSE","sud","01","nord","exterieur","Unique destination extérieure documentée ; aucun accès bas inventé.")
    connect("L31","01","sud","P3","nord")
    connect("L32","P3","ouest","C3O","est")
    connect("L33","C3O","nord","06","sud")
    connect("L34","P3","est","C3E","ouest")
    connect("L35","C3E","est","11","ouest")
    connect("V32","P3","descente","02","echelle_nord","vertical","Accueil → missions conservé, avec palier et trémie explicites.")
    connect("CHEF","02","porte_maitre","12","sud","porte","Porte visuellement fermée, interaction autorisée ; pas de seconde porte dans 12.")
    connect("L21","02","ouest","C2R","est_bas")
    connect("L22","C2R","est_haut","07","ouest")
    connect("L23","02","sud","P2","nord")
    connect("V21","P2","descente","03","echelle_nord","vertical","Missions → salle commune conservé ; le trou est sur le palier supérieur.")
    connect("L11","03","ouest","C1O","est")
    connect("L12","C1O","ouest","04","est")
    connect("L13","03","est","C1R","ouest_haut")
    connect("L14","C1R","ouest_bas","P1","est")
    connect("L15","03","sud","P1","nord","passage","Raccourci direct ; la boucle est une alternative, pas un détour obligatoire.")
    connect("L16","P1","ouest","05","est")
    connect("V10","P1","descente","P0","montee","vertical","Nouvelle paire pour le quatrième niveau ; puits supérieur et échelle basse à produire.")
    connect("L01","P0","ouest","08","est")
    connect("L02","P0","est","10","ouest")
    connect("L03","P0","sud","09","nord")
    for e in edges:
        if e["type"]=="vertical":
            e["axe_physique"]=e["id"]
            e["alignement"]= "Les deux extrémités partagent le même axe XY dans le monde ; placement métrique à valider après génération."
    plan={"titre":"Plan canonique interne — Guilde Treehouse", "version":1,"date":"2026-09-06", "statut":"Plan de référence, non intégré au moteur",
          "decisions_utilisateur":{"niveaux":"RDC + 3 étages", "exterieur":"Conserver l’existant et proposer", "formes":"Arrondies et organiques, pas de L anguleux ni de pans coupés"},
          "sources_prioritaires":["source/regles_acces.json","kit.json","source/base_kit.json"],
          "arbitrages":["La porte 02 nord → 12 prévaut sur l’ancienne entrée 03 NE du base_kit historique.",
                        "Terrasse → 01 → 02 → 03 reste la chaîne héritée ; des paliers clarifient les changements d’étage.",
                        "Accueil en R+3, missions en R+2, vie commune en R+1, dortoirs au RDC : aucune nouvelle entrée extérieure au RDC.",
                        "Les couloirs en retour sont des courbes ; leur topologie en boucle n’impose pas un contour polygonal."],
          "niveaux":[{"id":z,"nom":"RDC" if z==0 else f"R+{z}", "usage":{3:"Accueil / surveillance",2:"Missions / administration",1:"Vie commune / équipe",0:"Dortoirs"}[z], "pieces":LEVELS[z]} for z in [3,2,1,0]],
          "zones":nodes,"liaisons":edges,"schema":{"dimensions_par_niveau":[1200,620],"unite":"diagramme uniquement, pas coordonnées moteur"},
          "contrat_jouabilite":{"grille_px":8,"pied_test_px":16,"sprite_visuel_hypothese_px":32,"largeur_confort_passage_px":48,
                                 "palier_libre_devant_acces_px":32,"arrivee_hors_declencheur":True,"temporisation_ms":300,
                                 "relachement_action_requis":True,"triggers_par_centre_des_pieds":True,"trou_non_praticable":True,
                                 "scene_recommandee":"Une scène par étage ; pas un chargement par bout de couloir.",
                                 "statut":"Hypothèses de conception ; gabarit réel du personnage et moteur absents du dépôt."},
          "eclairage":{"source":"Généré dans les images maîtresses, puis séparé/contrôlé en post-traitement.",
                       "passages":"Contacts sur les joues et épaisseurs, centre du chemin lisible ; pas de bande noire transversale.",
                       "nord":"Renfoncement ombré et continuité du sol, pas une fausse porte ni un escalier mural.",
                       "tremies":"Vide plus sombre que le sol, épaisseur courbe, barreaux qui disparaissent en profondeur et rebord avant d’occultation.",
                       "nuit":"Même géométrie, reflets atténués ; pas de halos qui masquent les seuils."},
          "production":{"methode":"Générateur d’images → natif magenta → masques/calques → jour/nuit → PNG/Aseprite/Tiled.",
                        "interdit":"Dessiner les décors par code ou réintroduire les modules procéduraux refusés.",
                        "reste":"Sept zones de circulation sans master conforme ; deux instances peuvent partir de l’unique galerie générée, avec raccords à adapter."}}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"plan_canonique.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
    print(f"Plan écrit : {len(nodes)} zones, {len(edges)} liaisons, 4 niveaux.")

if __name__=="__main__":build()
