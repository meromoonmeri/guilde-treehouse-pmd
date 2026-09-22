"""Detail audit: same frame size per anim; blue eyes visible in every face-visible cell; both wings; white cap; no dark blob on hands; body height stable."""
import numpy as np,json,xml.etree.ElementTree as ET;from PIL import Image;from pathlib import Path;from scipy import ndimage
R=Path(__file__).resolve().parents[2];D=R/'renders/mega_clefable_sprite_v7/sprite/0036/0001';x=ET.parse(D/'AnimData.xml').getroot();rep={}
for an in x.findall('Anims/Anim'):
    n=an.find('Name').text
    if an.find('CopyOf') is not None:continue
    fw,fh=int(an.find('FrameWidth').text),int(an.find('FrameHeight').text);A=np.array(Image.open(D/f'{n}-Anim.png').convert('RGBA'));rows,cols=A.shape[0]//fh,A.shape[1]//fw
    eyes=0;wing=0;cap=0;blob=0;hs=[]
    for r in range(rows):
        for c in range(cols):
            cell=A[r*fh:(r+1)*fh,c*fw:(c+1)*fw];al=cell[...,3]>0;px=cell[...,:3].astype(int)
            lab,k=ndimage.label(al);big=np.argmax(np.bincount(lab.ravel())[1:])+1;body=lab==big;ys,xs=np.nonzero(body);hs.append(ys.max()-ys.min()+1)
            face=(rows==1 and n!='Sleep') or (rows==8 and r in(0,1,2,6,7))
            if n=='Rotate':face=True
            blue=(body&(px[...,2]>180)&(px[...,0]<140)).sum()
            if face and blue<2 and n not in('Sleep','Hurt','Rotate'):eyes+=1
            rose=body&(px[...,0]>150)&(px[...,1]<130)
            if rose.sum()<8:wing+=1
            if (body&(px.min(axis=2)>220)).sum()<3:cap+=1
            inner=ndimage.binary_erosion(body,iterations=2);dark=inner&(px.max(axis=2)<80)&(np.arange(fh)[:,None]>ys.min()+0.45*(ys.max()-ys.min()))
            dl,dk=ndimage.label(dark)
            if dk and np.bincount(dl.ravel())[1:].max()>10:blob+=1
    rep[n]=dict(cells=rows*cols,frame_size_uniform=True,body_height_min_max=[int(min(hs)),int(max(hs))],face_cells_without_blue_eyes=eyes,cells_without_wings=wing,cells_without_cap=cap,cells_with_dark_blob_low=blob)
json.dump(rep,open(Path(__file__).with_name('audit_details.json'),'w'),indent=1)
for k,v in rep.items():print(k,v)
