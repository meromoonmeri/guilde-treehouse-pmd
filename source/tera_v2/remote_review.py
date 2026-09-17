"""Exercise the catalogue-wide renderer on deliberately varied native silhouettes."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
from PIL import Image,ImageDraw
from catalogue_surface import load,catalogue,OUT
from prismatic import sheet,PHASES
sys.path.insert(0,str(Path(__file__).parent.parent/'transformations_v1'))
from assets import gif

CASES={'0025':'Pikachu','0081':'Magnemite','0092':'Gastly','0095':'Onix','0143':'Snorlax','0201':'Unown','0321':'Wailord','0355':'Duskull','0382':'Kyogre','0479':'Rotom','0497':'Serperior','0595':'Joltik'}

def main():
    index=catalogue();items=[];checks=[]
    for slot,name in CASES.items():
        path=slot+'/Idle-Anim.png';im,size,info=load(path,index)
        native=np.array(im);phases=[];folder=OUT/'remote_banks'/slot;folder.mkdir(parents=True,exist_ok=True)
        for phase in range(PHASES):
            result=sheet(im,size,phase);a=np.array(result)
            assert np.array_equal(a[:,:,3],native[:,:,3])
            assert np.array_equal(a[native[:,:,3]==0],native[native[:,:,3]==0])
            result.save(folder/f'phase_{phase:02d}.png')
            phases.append(result.crop((0,0,*size)))
        (folder/'credits.txt').write_text(info.pop('credits'))
        checks.append({**info,'phases_tested':24,'alpha_exact':True,'transparent_rgb_exact':True,'source_sha256':hashlib.sha256(im.tobytes()).hexdigest()})
        items.append((name,im.crop((0,0,*size)),phases))
        print(name,im.size,size,flush=True)
    frames=[]
    for phase in range(PHASES):
        board=Image.new('RGB',(768,540),(18,27,41));draw=ImageDraw.Draw(board)
        for i,(name,native,phases) in enumerate(items):
            box=native.getbbox();x=i%4*192;y=i//4*180
            for side,image in enumerate([native,phases[phase]]):
                image=image.crop(box);factor=min(3,84/image.width,128/image.height)
                image=image.resize((max(1,round(image.width*factor)),max(1,round(image.height*factor))),Image.Resampling.NEAREST)
                board.paste(image,(x+side*96+(96-image.width)//2,y+140-image.height),image)
            draw.text((x+8,y+150),name+'  natif / verre',fill='white')
        frames.append(board)
    gif(frames,OUT/'review/catalogue_glass_sample.gif',[70,60,70]*8)
    frames[6].save(OUT/'review/catalogue_glass_sample.png')
    (OUT/'remote_verification.json').write_text(json.dumps({'pin':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','remote_sheets_rendered':len(checks),'checks':checks,'preview':'Frozen first native pose with 24 animated light phases; complete sheets are tested and saved','runtime_PMDO':'NOT INTEGRATED OR TESTED'},indent=2)+'\n')
    report=json.loads((OUT/'catalogue_report.json').read_text());report['rendered_remote_sheets']=len(checks);report['remaining_remote_sheets_unrendered']=report['animation_sheet_count']-len(checks)
    (OUT/'catalogue_report.json').write_text(json.dumps(report,indent=2)+'\n')
    # Coverage status is per exact source file, never per species name alone.
    done={c['source'] for c in checks}
    with (OUT/'spritecollab_catalogue.csv').open() as f:rows=list(csv.DictReader(f))
    for r in rows:
        if r['sprite_relative_path'] in done:r['processing_state']='24_phases_rendered_alpha_verified_not_PMDO'
    with (OUT/'spritecollab_catalogue.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=='__main__':main()
