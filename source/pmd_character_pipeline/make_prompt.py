"""Prepare a per-request image-generation prompt. Does NOT call or retrain a model."""
import argparse,json
from pathlib import Path
C=json.loads(Path(__file__).with_name('contract.json').read_text())
def make(brief,kind,emotion='Normal',direction='Down'):
 species=brief.get('species','')
 if not species or species.startswith('<'):raise ValueError('Specify the Pokemon species first')
 refs=brief.get('references',[])
 if not refs:raise ValueError('Add verified canonical/native references before generation')
 identity=f"Pokemon: {species}. Form/design: {brief.get('form_description','canonical form')}. Individual traits/accessories: {brief.get('custom_traits','none')}. Asymmetry that must remain consistent: {brief.get('asymmetry','must be checked against references')}."
 common=identity+' Use the supplied canonical design and Chunsoft PMD reference images as the anatomical and style guide. This output is a drawing/reference draft for deliberate pixel cleanup, not an engine-ready asset. No text, labels, watermark, interface or decorative frame. Do not invent features or change body proportions between views. '
 if kind=='portrait':
  if brief.get('spritecollab_slot') in C['portrait'].get('blocked_subject_slots',{}):
   raise ValueError(C['portrait']['blocked_subject_slots'][brief['spritecollab_slot']])
  normal=brief.get('normal_portrait_reference')
  if emotion!='Normal' and (not normal or normal not in refs):
   raise ValueError('Non-Normal expressions require the native/approved Normal portrait explicitly included in references')
  slot=brief.get('spritecollab_slot') or ''
  if slot.split('/')[0]=='0026' or 'raichu' in species.lower():
   common+=' Raichu expressions must be natural to its rodent muzzle: NO human lips, lip biting/sucking, visible teeth, human grimaces or invented facial folds. Pain is primarily expressed through eyelids and a small closed animal mouth. '
  if slot.split('/')[0]=='0564' or any(n in species.lower() for n in ['tirtouga','carapagos']):
   common+=' Keep the approved Normal turtle face and its beak/nostril anatomy; use natural eye and beak acting, never human lips or a redesigned muzzle. Preserve all previously approved portraits. '
  common+=' The supplied Normal portrait is the FIXED anatomical master. Preserve the exact face silhouette, proportions, muzzle, nose, cheek placement, eye implantation and characteristic design, ears, markings, perspective and framing. Only eyelids, brows and mouth may move naturally for the expression; never replace or redesign facial traits. Begin with one restrained expression trial, not a sheet. Technical compliance cannot excuse anatomical drift. '
  if emotion not in C['portrait']['emotions']:raise ValueError('Use a configured emotion slot; describe custom nuance in the brief')
  return common+f"Create ONE emotion portrait, {emotion}, not a contact sheet. Tight expressive head composition intended for a 40 by 40 pixel PMD Explorers portrait. Make the large drawing roughly 400 by 400 compositionally; final 40 by 40 raster and palette will be constructed and checked separately. When deriving an expression, keep the Normal portrait view and framing exactly; do not invent a new face angle or head tilt. Derive natural eyelid, brow and mouth movements from its existing facial anatomy. Keep important ears, muzzle and species identifiers legible at native scale. Emulate the softly clustered, illustrated Chunsoft portrait look: colored dark outlines, controlled cel shading, a few opaque hand-placed blend colors, no uniform heavy pure-black outline, no smooth 3D rendering, photorealism, bloom or noisy dithering. Use the designated emotion cell from the user-provided template.png as the priority background reference; Extra_Backgrounds.png requires an explicit chosen cell. Do not invent a landscape background. Reserve about three background colors plus a blend color in a total intended fifteen-color palette. Filled final portraits must be entirely opaque including their background; no magenta or transparent holes. "+brief.get('emotion_notes',{}).get(emotion,'')
 if direction not in C['sprite']['directions']:raise ValueError('Unknown PMD direction')
 return common+f"Create ONE full-body Idle key-pose guide facing {direction}. Match the exact oblique PMD dungeon camera, native reference body scale and grounded center. Keep every limb, marking and attachment anatomically consistent. Crisp small pixel clusters, readable silhouette, restrained shading and a planned fifteen-visible-color palette shared with ALL future animations. Use flat solid magenta only as a removable intermediate matte if transparency is unavailable, with no magenta on the character. No ground, scene, painted shadow, blur, bloom, alpha gradients or illustration background. Do NOT draw technical offset markers: they will be authored as separate PNG sheets, as will the engine shadow. Do not produce the final 8-direction animation grid in this drawing; approved native-size poses will be registered, retouched and animated separately. "
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('brief',type=Path);p.add_argument('kind',choices=['portrait','sprite']);p.add_argument('--emotion',default='Normal');p.add_argument('--direction',default='Down');a=p.parse_args();print(make(json.loads(a.brief.read_text()),a.kind,a.emotion,a.direction))
