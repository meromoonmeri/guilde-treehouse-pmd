"""Review generated Fire cardinal candidates on four existing head profiles.
These are explicit fit proposals, not new verified anatomical masks or all-species coverage.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from prismatic import glass,PHASES
sys.path.insert(0,str(Path(__file__).parent.parent/'transformations_v1'))
from crown_attachment.attach import ROOT,load_profiles,inspect_profile,seat_from_markers,DIRECTIONS
from assets import gif
OUT=ROOT/'exports/tera_v2'

def main():
    profiles=load_profiles();names=['charizard','mega_charizard_x','gigantamax_charizard','tirtouga_v5'];directions=[0,2,4,6]
    sources={name:(Image.open(ROOT/profiles[name]['sprite_dir']/'Idle-Anim.png').convert('RGBA'),[r for r in inspect_profile(name,profiles[name])['records'] if r['action']=='Idle' and r['frame']==0]) for name in names}
    frames=[];placements=[]
    for phase in range(PHASES):
        board=Image.new('RGB',(768,896),(18,27,41));draw=ImageDraw.Draw(board)
        for row,d in enumerate(directions):
            crown=Image.open(OUT/'crowns'/f'CROWN_V2_fire_{DIRECTIONS[d]}.png').convert('RGBA')
            a=np.array(crown);mask=a[:,:,3]>0;mask[:64]=False;yy,xx=np.where(mask)
            anchor=[float((xx.min()+xx.max())/2),int(yy.max()-1)];band_width=int(xx.max()-xx.min()+1)
            for col,name in enumerate(names):
                native,records=sources[name];r=next(r for r in records if r['row']==d);w,h=r['frame_size']
                cell=native.crop((0,d*h,w,(d+1)*h));scale=1 if name=='gigantamax_charizard' else 2
                ground=[col*192+96,row*224+192]
                actor=glass(cell,phase).resize((w*scale,h*scale),Image.Resampling.NEAREST)
                target_width=r['head_band_width']*scale;factor=target_width/band_width
                size=(max(1,round(crown.width*factor)),max(1,round(crown.height*factor)))
                accessory=glass(crown,phase).resize(size,Image.Resampling.NEAREST)
                extra=[0,2] if (name,d)==('tirtouga_v5',4) else [0,0]
                fitted_offset=[r['seat_offset'][i]+extra[i] for i in range(2)]
                offset=seat_from_markers(r['head'],r['shadow'],fitted_offset,scale)
                seat=[ground[i]+offset[i] for i in range(2)]
                origin=[round(seat[i]-anchor[i]*size[i]/crown.size[i]) for i in range(2)]
                layer=Image.new('RGBA',board.size);layer.alpha_composite(actor,(ground[0]-r['shadow'][0]*scale,ground[1]-r['shadow'][1]*scale))
                layer.alpha_composite(accessory,origin);board.paste(layer,(0,0),layer)
                draw.text((col*192+5,row*224+208),name.replace('gigantamax_charizard','Gmax')+' '+DIRECTIONS[d],fill='white')
                if phase==0:placements.append({'profile':name,'direction':d,'native_frame':0,'preview_scale':scale,'seat_world':seat,'crown_origin':origin,'band_anchor':anchor,'band_width':band_width,'new_asset_seat_adjustment':extra,'status':'manual width/seat profile reused, new crown depth and anatomy require visual review; no horn/ear masks'})
        frames.append(board)
    gif(frames,OUT/'review/fire_attached_glass.gif',[70,60,70]*8)
    frames[6].save(OUT/'review/fire_attached_glass.png')
    (OUT/'attached_review.json').write_text(json.dumps({'placements':placements,'phase_count':PHASES,'body_pose':'first native Idle pose only','coverage':'four local profiles x four Fire cardinal models; no diagonal claim','runtime_PMDO':'NOT TESTED'},indent=2)+'\n')

if __name__=='__main__':main()
