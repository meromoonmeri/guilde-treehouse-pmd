"""Export crown model candidates and non-destructive prismatic phase banks."""
from pathlib import Path
import sys,json,hashlib,math,shutil
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).parent.parent/'transformations_v1'))
from prismatic import glass,sheet,PHASES
from crown_attachment.attach import ROOT,load_profiles,inspect_profile
from assets import gif
OUT=ROOT/'exports/tera_v2';SRC=Path(__file__).parent
for n in ['crowns','review','surface_banks']:(OUT/n).mkdir(parents=True,exist_ok=True)
DIRECTIONS=['D','DR','R','UR','U','UL','L','DL']

MODELS={
 'fire_cardinals':(['fire']*4,2,2,[0,2,4,6]),
 'water_corrected_eight':(['water']*8,4,2,list(range(8))),
 'normal_flying_grass_corrected':(['normal','flying','grass'],3,1,[0]*3),
 'fighting_poison_ground':(['fighting','poison','ground'],3,1,[0]*3),
 'rock_bug_steel':(['rock','bug','steel'],3,1,[0]*3),
 'electric_psychic_ice':(['electric','psychic','ice'],3,1,[0]*3),
 'dragon_dark_fairy':(['dragon','dark','fairy'],3,1,[0]*3),
 'ghost_stellar':(['ghost','stellar'],2,1,[0]*2)
}

def crowns():
    records=[]
    for source,(types,cols,rows,dirs) in MODELS.items():
        raw=Image.open(SRC/'generation'/f'{source}.png').convert('RGBA');w,h=raw.width/cols,raw.height/rows
        for i,(kind,direction) in enumerate(zip(types,dirs)):
            box=(round(i%cols*w)+8,round(i//cols*h)+8,round((i%cols+1)*w)-8,round((i//cols+1)*h)-8)
            im=raw.crop(box);a=np.array(im)
            # Exact-background family, not a broad pink removal on the crown's facets.
            magenta=(a[:,:,0]>155)&(a[:,:,2]>155)&(a[:,:,1]<28)
            a[magenta]=0;im=Image.fromarray(a)
            bounds=im.getbbox()
            if not bounds:raise ValueError(source)
            im=im.crop(bounds);im.thumbnail((54,68),Image.Resampling.NEAREST)
            native=Image.new('RGBA',(64,80));native.alpha_composite(im,((64-im.width)//2,75-im.height))
            name=f'CROWN_V2_{kind}_{DIRECTIONS[direction]}.png'
            destination=OUT/('review/rejected_models' if kind=='stellar' else 'crowns')/name
            destination.parent.mkdir(parents=True,exist_ok=True);native.save(destination)
            records.append({'type':kind,'requested_direction':direction,'file':str(destination.relative_to(OUT)),'source':'source/tera_v2/generation/'+source+'.png','crop':box,'status':'rejected_stellar_statue_identity' if kind=='stellar' else 'model_candidate_not_anatomically_registered','orientation':'requested generated angle; not certified','notes':'Stellar statue and exact 18+18 motifs need correction/review' if kind=='stellar' else 'No wearer head/body; front jewel plain. Inherent type emblems may include a skull, ghost, mask or eye.'})
    rejected={'water_cardinals.png':'Rejected hanging loops below fountain; replaced through generation','normal_flying_grass.png':'Rejected oversized dangling rings below Normal/Grass; replaced through generation'}
    manifest={'records':records,'types_drawn':sorted({r['type'] for r in records}),'type_count':len({r['type'] for r in records}),'rejected_sources':rejected,'missing_direction_views':{'fire':[1,3,5,7],'water':[],'other_17_types':[1,2,3,4,5,6,7]},'known_model_issues':{'stellar':'Rejected for use: statue is not faithful enough; exact 18+18 motif counts unverified','flying':'Generated replacement balloon count is not faithful to the required two red plus two green; regeneration required'},'warning':'View presence is not verified direction fidelity. Water DL especially needs review; no automatic replacement of previously fitted crowns.'}
    (OUT/'crown_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    front=[r for r in records if r['requested_direction']==0]
    board=Image.new('RGB',(5*192,4*208),(18,27,41));draw=ImageDraw.Draw(board)
    for i,r in enumerate(front):
        x=i%5*192;y=i//5*208
        im=Image.open(OUT/r['file']).resize((128,160),Image.Resampling.NEAREST)
        board.paste(im,(x+32,y+8),im);draw.text((x+12,y+180),r['type'].upper(),fill='white')
    board.save(OUT/'review/all_crown_models.png')
    return manifest

def surfaces():
    profiles=load_profiles();manifest={'phase_count':PHASES,'phase_ticks':4,'light_period_ticks':PHASES*4,'action_timing':'Unchanged native XML; actor frame and surface phase are independent clocks','runtime_PMDO':'NOT INTEGRATED OR TESTED','profiles':{}}
    count=0;cells=0;hashes={};checks=[]
    for name,profile in profiles.items():
        report=inspect_profile(name,profile);path=ROOT/profile['sprite_dir'];folder=OUT/'surface_banks'/name;folder.mkdir(parents=True,exist_ok=True)
        sources={}
        for r in report['records']:sources[r['source_action']]=r['frame_size']
        entries=[]
        for action,size in sources.items():
            file=path/f'{action}-Anim.png';sha=hashlib.sha256(file.read_bytes()).hexdigest();hashes[str(file.relative_to(ROOT))]=sha
            im=Image.open(file).convert('RGBA');original=np.array(im);exported=[]
            for phase in range(PHASES):
                out=sheet(im,size,phase);arr=np.array(out)
                assert np.array_equal(original[:,:,3],arr[:,:,3])
                assert np.array_equal(original[original[:,:,3]==0],arr[original[:,:,3]==0])
                target=folder/f'phase_{phase:02d}'/file.name;target.parent.mkdir(exist_ok=True);out.save(target)
                exported.append(str(target.relative_to(OUT)));count+=1;cells+=im.width//size[0]*(im.height//size[1])
            assert np.array_equal(np.array(sheet(im,size,0)),np.array(sheet(im,size,PHASES)))
            entries.append({'action':action,'native_cell':size,'sheet_size':im.size,'source':str(file.relative_to(ROOT)),'phase_files':exported})
        shutil.copyfile(path/'AnimData.xml',folder/'AnimData.xml')
        assert (folder/'AnimData.xml').read_bytes()==(path/'AnimData.xml').read_bytes()
        manifest['profiles'][name]={'source_dir':profile['sprite_dir'],'active':profile['active'],'xml':'surface_banks/'+name+'/AnimData.xml','actions':entries,'declared_actions_without_local_sources':report['skipped_actions']}
        print(name,len(entries),'unique sheets x',PHASES,'phases',flush=True)
    for p,sha in hashes.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha
    verification={'native_sheet_count':count//PHASES,'exported_phase_sheets':count,'cell_phase_checks':cells,'alpha_exact':True,'transparent_rgb_exact':True,'native_action_xml_exact':True,'phase_0_equals_phase_24':True,'source_hashes_preserved':hashes,'source_scope':'six local sprite folders only; no claim of remote catalogue rendered','runtime_PMDO':'NOT INTEGRATED OR TESTED'}
    (OUT/'surface_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'surface_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    # Native action timing plus independent 96-tick light clock: common period 480 ticks.
    for name in ['charizard','gigantamax_charizard','tirtouga_v5']:
        profile=profiles[name];path=ROOT/profile['sprite_dir'];records=[r for r in inspect_profile(name,profile)['records'] if r['action']=='Idle']
        im=Image.open(path/'Idle-Anim.png').convert('RGBA');frames=max(r['frame'] for r in records)+1
        durations=[next(r['ticks'] for r in records if r['frame']==i) for i in range(frames)]
        total=math.lcm(sum(durations),96);images=[]
        for tick in range(0,total,2):
            native_tick=tick%sum(durations);f=0
            while native_tick>=durations[f]:native_tick-=durations[f];f+=1
            board=Image.new('RGB',(768,576),(18,27,41));draw=ImageDraw.Draw(board)
            for d in range(8):
                r=next(r for r in records if r['row']==d and r['frame']==f);w,h=r['frame_size']
                native=im.crop((f*w,d*h,(f+1)*w,(d+1)*h));crystal=glass(native,tick//4)
                # Same native dimensions on both sides; 2x review zoom for small actors.
                scale=1 if name=='gigantamax_charizard' else 2
                for side,picture in enumerate([native,crystal]):
                    picture=picture.resize((w*scale,h*scale),Image.Resampling.NEAREST)
                    x=d%4*192+side*96+48-r['shadow'][0]*scale;y=d//4*288+210-r['shadow'][1]*scale
                    if name=='gigantamax_charizard':
                        # Large actor: show one original/crystal pair per direction in a larger board below.
                        continue
                    board.paste(picture,(x,y),picture)
                draw.text((d%4*192+5,d//4*288+260),DIRECTIONS[d]+'  natif / verre',fill='white')
            if name=='gigantamax_charizard':
                board=Image.new('RGB',(768,576),(18,27,41));draw=ImageDraw.Draw(board)
                for d in range(8):
                    r=next(r for r in records if r['row']==d and r['frame']==f);w,h=r['frame_size'];native=im.crop((f*w,d*h,(f+1)*w,(d+1)*h));crystal=glass(native,tick//4)
                    board.paste(crystal,(d%4*192+(192-w)//2,d//4*288+230-r['shadow'][1]),crystal)
                    draw.text((d%4*192+8,d//4*288+260),DIRECTIONS[d],fill='white')
            images.append(board)
        gif(images,OUT/'review'/f'{name}_glass_eight.gif')
        images[len(images)//3].save(OUT/'review'/f'{name}_glass_eight.png')
    return verification

if __name__=='__main__':
    crowns();print(json.dumps(surfaces(),indent=2))
