"""Record the actual visual review, separate from numerical palette checks.
Run after build.py; repeated builds reset inspection status until this review is reapplied.
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/caps_terrasses_v4'
REVIEWS={
'07':('A_REGENERER','Roche en petits galets verticaux et couronne en chapelet : le motif ne reprend pas la référence Métano. La palette verrouillée ne corrige pas cette erreur de dessin.'),
'08':('RETENU_VISUELLEMENT','Couronne continue au retour concave ; herbe et paroi se rejoignent sans bande détachée visible. Grain plus dense sur le flanc droit ; pas de certification des tuiles pixel à pixel.'),
'09':('RETENU_VISUELLEMENT','Deux paliers distincts ; les couronnes suivent les arrondis et rejoignent les faces. Matériau et teintes proches de la référence après correction.'),
'10':('RETENU_VISUELLEMENT','Deux balcons lisibles, couronne et roche cohérentes dans les coupes inspectées. Extrémités de couronne un peu relevées : détail à surveiller lors du placement. Recalage vertical documenté.'),
'11':('A_REGENERER','Rebord lisse en double bande et gros blocs trop simplifiés, différents de la couronne et du grain Métano demandés. Ne pas présenter comme une falaise conforme au contrôle de dessin.'),
'12':('RETENU_VISUELLEMENT','Couronne irrégulière continue autour du renfoncement ; retour rocheux ombré cohérent, herbe jointe au rebord dans le gros plan.'),
'13':('RETENU_VISUELLEMENT','Couronne découpée et retour arrondi cohérents avec la présentation Métano. Coupe choisie manuellement sur le vrai bord avant, pas sur le bord arrière du plateau.'),
'14':('RETENU_VISUELLEMENT','Retour concave lisible et rebord continu. Ajout à la palette de l’ombre mauve native 96,56,88, vérifiée dans Cliffs, pour éviter d’éclaircir artificiellement le creux. La profondeur reste une interprétation générée.'),
'15':('RETENU_VISUELLEMENT','Trois niveaux distincts et raccords herbe/roche lisibles ; couronnes locales cohérentes. Les extrémités ne sont pas des autotiles certifiés.'),
'16':('RETENU_VISUELLEMENT','Couronne fine suivant le balcon ; même famille de roche et d’herbe. Texture répétitive sur la grande face : observation conservée, pas une preuve de seamlessness entre cartes.')}

def main():
 m=json.loads((OUT/'manifest.json').read_text());entries=[]
 pins=json.loads((HERE/'visual_review_pins.json').read_text())
 for z in m['zones']:
  assert pins[z['id']]['raw_sha256']==z['raw_sha256'], 'Source changed: a new visual review is required'
  assert pins[z['id']]['terrain_rgba_sha256']==hashlib.sha256(Image.open(OUT/z['terrain']).convert('RGBA').tobytes()).hexdigest(), 'Corrected terrain changed: review again'
 board=Image.open(OUT/'PLANCHE_10_FACE_MER.png').convert('RGB');d=ImageDraw.Draw(board)
 crops=Image.open(OUT/'AUDIT_BORDURES_AVANT_APRES.png').convert('RGB');cd=ImageDraw.Draw(crops)
 for i,z in enumerate(m['zones']):
  status,note=REVIEWS[z['id'][:2]];z['visual_status']=status;z['visual_note']=note
  entries.append({'id':z['id'],'status':status,'note':note,'scope':'review of full scene and native-size crown crop; not an engine test or tile-identity proof'})
  x=i%2*900;y=i//2*300;color='#f29f8d' if status=='A_REGENERER' else '#badba2'
  d.rectangle((x+8,y+274,x+882,y+297),fill='#263c46');d.text((x+14,y+277),'A REGENERER - dessin non retenu' if status=='A_REGENERER' else 'Retenu visuellement - palette native verrouillee',fill=color)
  cd.text((900,180+i*200+8),'A REGENERER' if status=='A_REGENERER' else 'INSPECTE',fill=color)
 board.save(OUT/'PLANCHE_10_FACE_MER.png',optimize=True);crops.save(OUT/'AUDIT_BORDURES_AVANT_APRES.png',optimize=True)
 (OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
 report={'status':'PARTIEL_DESSIN','generated':10,'retained_after_visual_review':8,'to_regenerate':2,'palette_membership_checks_passed':10,'canonical_shape_identity_proved':False,'reason_not_regenerated_this_turn':'image tool refused the 07 revision: limit of 10 generations reached; no revision file was produced','entries':entries}
 (HERE/'audit_visuel.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('Visual audit recorded: 8 retained, 07 and 11 rejected for shape/material drawing.')
if __name__=='__main__':main()
