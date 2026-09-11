"""Vérifie les plans Treasure Town et le véritable cycling indexé, fichier et navigateur."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import json
import numpy as np
import os
import struct
import zlib
from verify_falaise import references, expected, verify_ase, verify_tiled, image
from verify_falaise_browser import actual, visual_delta
from prepare_zones_tt import FLOW

R=Path(__file__).resolve().parents[1]
S=R/'source/zones_treasure_town'
C=R/'.cache/tt-tests'


def verify_indexed(path,indices,palettes):
    raw=path.read_bytes();header=struct.unpack_from('<IHHHHHIH',raw)
    h,w=indices.shape;assert header==(len(raw),0xA5E0,len(palettes),w,h,8,1,250)
    p=128;cel=None
    for f,target in enumerate(palettes):
        size,magic,count,duration=struct.unpack_from('<IHHH',raw,p);assert magic==0xF1FA and duration==250
        end=p+size;p+=16;pal=None;seen_cel=False
        for _ in range(count):
            length,kind=struct.unpack_from('<IH',raw,p);d=raw[p+6:p+length]
            if kind==0x2019:
                n,first,last=struct.unpack_from('<III',d);assert (n,first,last)==(len(target),0,len(target)-1)
                pal=[list(struct.unpack_from('<HBBBB',d,20+i*6)[1:]) for i in range(n)]
            elif kind==0x2005:
                layer,x,y,opacity,typ,z=struct.unpack_from('<HhhBHh',d);assert (layer,x,y,opacity,z)==(0,0,0,255,0)
                if f==0:
                    assert typ==2 and struct.unpack_from('<HH',d,16)==(w,h)
                    cel=np.frombuffer(zlib.decompress(d[20:]),dtype=np.uint8).reshape(h,w)
                    assert np.array_equal(cel,indices)
                else:assert typ==1 and struct.unpack_from('<H',d,16)[0]==0
                seen_cel=True
            p+=length
        assert p==end and seen_cel and pal==target
        assert np.array_equal(np.asarray(pal,np.uint8)[cel],np.asarray(target,np.uint8)[indices])
    assert p==len(raw)


def verify():
    C.mkdir(parents=True,exist_ok=True);configs=json.loads((S/'layouts.json').read_text());reports=[]
    for name,cfg in configs.items():
        root=R/'paysages'/name;m=json.loads((root/'kit.json').read_text());size=tuple(m['dimensions']);frames=m['animation']['frames']
        assert size==tuple(cfg['size']) and m['regles']['structures'] is False
        ids={d['id']:i for i,d in enumerate(m['calques'])}
        assert m['base_start']==ids['terrain'] and m['regles']['plans_generes_separement']
        assert all(f'cascade_{n:02d}' in ids for n in range(1,len(FLOW.get(name,[]))+1))
        report={'id':name,'dimensions':list(size),'calques':len(m['calques']),'texture_treasure_town_controle_visuel':True,
                'plans_generes_separement':True,'indices_fixes':True,'palettes_animees':True,
                'cascades_et_ecume_separees':True,'chaque_cascade_independante':True,'nuages_deux_plans_wrap':True,'ambiances':[]}
        for mode in ['jour','nuit']:
            refs=references(root,m,mode);f=m['fichiers'][mode]
            assert np.array_equal(np.array(expected(refs,0,size)),np.array(image(root/f['composition'])))
            assert np.array_equal(np.array(expected(refs,0,size,base_start=m['base_start'])),np.array(image(root/f['base'])))
            if mode=='jour':
                assert np.array_equal(refs[ids['terrain']].array,np.array(image(S/name/'terrain_genere.png')))
                assert np.array_equal(refs[ids['06_reliefs']].array,np.array(image(S/name/'reliefs.png')))
            for i,ref in enumerate(refs):
                assert np.array_equal(np.array(ref.at(0)),np.array(ref.at(frames)))
                if ref.spec and ref.spec['kind']=='stars':
                    moon=(ref.groups==0)&(ref.array[:,:,3]>0)
                    for phase in range(24):assert np.array_equal(np.array(ref.at(phase))[moon],ref.array[moon])
                if ref.spec and ref.spec['kind']=='palette_cycle':
                    spec=ref.spec;assert spec['translated_pixels'] is False
                    indices=np.array(Image.open(root/spec['indices'])).astype(int)
                    tables=np.array(spec['palettes'],np.uint8)
                    assert set(np.unique(indices)).issubset(set(range(tables.shape[1])))
                    assert len({x.tobytes() for x in tables})>=8
                    assert np.array_equal(tables[:,spec['static_indices']],np.repeat(tables[0:1,spec['static_indices']],len(tables),axis=0))
                    alpha=np.array(ref.at(0))[:,:,3]
                    for phase in range(ref.period):
                        current=np.array(ref.at(phase))
                        assert np.array_equal(current,tables[phase][indices])
                        assert np.array_equal(current[:,:,3],alpha), 'La forme se déplace au lieu de cycler'
                    assert not np.array_equal(np.array(ref.at(0)),np.array(ref.at(ref.period//2)))
                    key=m['calques'][i]['id'];asset=f['palette_assets'][key]
                    verify_indexed(root/asset['aseprite_indexe'],indices.astype(np.uint8),spec['palettes'])
            far=refs[ids['02_nuages_lointains']];near=refs[ids['03_nuages_proches']]
            assert far.spec['step']==1 and near.spec['step']==2
            for cloud in [far,near]:
                assert cloud.spec['kind']=='scroll' and cloud.array[:,:,3].any()
                assert np.array_equal(np.array(cloud.at(1)),np.roll(cloud.array,-cloud.spec['step'],axis=1))
                assert not np.array_equal(np.array(cloud.at(0)),np.array(cloud.at(12)))
                assert np.array_equal(np.roll(np.array(cloud.at(cloud.period-1)),-cloud.spec['step'],axis=1),np.array(cloud.at(0))), 'Raccord wrap incorrect'
            if mode=='jour':
                cloud_sum=Image.new('RGBA',size);cloud_sum.alpha_composite(far.at(0));cloud_sum.alpha_composite(near.at(0))
                assert np.array_equal(np.array(cloud_sum),np.array(image(S/name/'nuages.png'))), 'Nuages perdus dans la séparation'
            if name=='plateaux':
                assert refs[ids['brume_wrap']].spec['kind']=='scroll'
                brume=refs[ids['brume_wrap']].array
                assert np.array_equal(brume[:,0],brume[:,-1]), 'Couture dans la mer de nuages'
            if name in ['etang','cascades']:
                assert refs[ids['05_eau_cycle']].spec['kind']==refs[ids['ecume']].spec['kind']=='palette_cycle'
                for n in range(1,len(FLOW[name])+1):
                    ref=refs[ids[f'cascade_{n:02d}']]
                    assert ref.spec['kind']=='palette_cycle' and ref.array[:,:,3].any()
                    assert ref.spec['phase_offset']==((n-1)*2)%8
            verify_ase(root/f['aseprite'],refs,size,frames,250)
            verify_tiled(root/f['tiled'],refs,size,frames,250)
            report['ambiances'].append({'id':mode,'PNG_Aseprite_Tiled':'identiques','frames_verifiees':frames,
                                       'calques_cycling':list(f['palette_assets'])})
        (root/'controle_qualite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        reports.append(report);print('PASS fichiers',name,flush=True)
    launch={'headless':True,'args':['--no-sandbox']}
    if os.environ.get('FALAISE_CHROMIUM'):launch['executable_path']=os.environ['FALAISE_CHROMIUM']
    errors=[];network=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch);context=browser.new_context(offline=True,viewport={'width':1280,'height':1000})
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http://','https://')) else None)
        page.goto((R/'apercu_falaise.html').as_uri());page.wait_for_selector('body[data-ready=true]',timeout=60000);page.evaluate('FALAISE.pause()')
        for report in reports:
            name=report['id'];root=R/'paysages'/name;m=json.loads((root/'kit.json').read_text());size=tuple(m['dimensions']);maximum=0
            page.click(f'[data-scene="{name}"]')
            for mode in ['jour','nuit']:
                page.click(f'[data-sky="{mode}"]');refs=references(root,m,mode)
                for f in [0,1,3,7,12,m['animation']['frames']-1]:
                    page.evaluate('(n)=>FALAISE.setFrame(n)',f);delta=visual_delta(actual(page),expected(refs,f,size));maximum=max(maximum,delta)
                    assert delta<=2,(name,mode,f,delta)
                page.evaluate('FALAISE.setFrame(0)')
                for i in range(len(refs)):
                    box=page.locator(f'input[data-layer="{i}"]')
                    if box.is_disabled():continue
                    box.uncheck();delta=visual_delta(actual(page),expected(refs,0,size,excluded=i));maximum=max(maximum,delta)
                    assert delta<=2,(name,mode,i,delta)
                    page.locator(f'input[data-layer="{i}"]').check()
                if name!='plateaux':assert page.locator('#cycling').is_visible()
                page.screenshot(path=str(C/f'{name}_{mode}.png'),full_page=True)
            page.evaluate('FALAISE.setFrame(0)');page.click('#base');frozen=actual(page);page.click('#animation')
            page.wait_for_function('FALAISE.getState().frame>=3',timeout=4000)
            assert np.array_equal(actual(page),frozen)
            page.click('#animation');page.click('#composite');page.evaluate('FALAISE.setFrame(0)')
            for width in [320,390,768,1280]:
                page.set_viewport_size({'width':width,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            report.update(comparaisons_navigateur=12,erreur_max_premultiplie=round(maximum,4),terrain_fixe=True,hors_ligne=True,mobile=True)
            print('PASS navigateur',name,maximum,flush=True)
        assert not errors,errors;assert not network,network;browser.close()
    for report in reports:
        report['erreurs_js']=errors;report['requetes_reseau']=network
        (R/'paysages'/report['id']/'controle_qualite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return reports


if __name__=='__main__':verify()
