from pathlib import Path
from PIL import Image
import numpy as np
import json
R=Path(__file__).resolve().parents[2];O=R/'renders/cote_cendres_passage_v2';P=O/'cote_cendres_passage'
m=json.loads((O/'manifest.json').read_text())
for i in range(m['frames']):
 c=Image.new('RGBA',tuple(m['size']))
 names=[f'01_lave_visqueuse_{i:03}',f'02_lueur_rives_{i:03}']+m['static_layers']+[f'07_colonne_{k:02}_{i:03}' for k in range(8)]
 for n in names:c.alpha_composite(Image.open(P/f'cendres_v2_{n}.png').convert('RGBA'))
 assert np.array_equal(np.array(c),np.array(Image.open(P/f'cendres_v2_scene_{i:03}.png')))
 assert np.all(np.array(c)[:,:,3]==255)
m['tests']['all_64_saved_frames_recompose']=True
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('64 saved frames recompose exactly from 10 animated groups and 4 static layers.')
