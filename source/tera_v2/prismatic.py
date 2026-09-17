"""Species-independent, alpha-preserving crystal surface renderer.
This is an offline reference implementation, NOT an installed PMDO shader.
Input: any native RGBA animation cell. No species IDs, anatomy markers or crown
placement are needed. The original action timeline remains independent of light phase.
"""
import numpy as np
import cv2
from PIL import Image

PHASES = 24

def glass(cell, phase):
    a=np.asarray(cell.convert('RGBA'))
    mask=a[:,:,3]>0
    if not mask.any():return cell.convert('RGBA').copy()
    yy,xx=np.mgrid[:a.shape[0],:a.shape[1]]
    phase=(phase%PHASES)/PHASES
    theta=phase*2*np.pi
    # Explicit exterior zeros keep fully opaque / edge-touching cells finite.
    padded=np.pad(mask.astype(np.uint8),1,constant_values=0)
    distance=cv2.distanceTransform(padded,cv2.DIST_L2,3)[1:-1,1:-1]
    # Local curvature controls the rim; triangular panes give the interior glass volume.
    ny,nx=np.gradient(cv2.GaussianBlur(distance,(0,0),.8)) if min(mask.shape)>1 else (np.zeros_like(distance),np.zeros_like(distance))
    norm=np.maximum(1,np.sqrt(nx*nx+ny*ny));nx/=norm;ny/=norm
    py,px=np.where(mask);width=px.max()-px.min()+1;height=py.max()-py.min()+1
    cellsize=max(3,min(12,round(min(width,height)/4)))
    u=(xx-px.min())/cellsize;v=(yy-py.min())/cellsize
    tri=((u%1)+(v%1)>1).astype(float)
    pane=(np.floor(u)*.71+np.floor(v)*1.13+tri*.48)
    normal_x=np.sin(pane*2.1)*.7+nx*.3
    normal_y=np.cos(pane*1.7)*.7+ny*.3
    facing=np.clip(normal_x*np.cos(theta)+normal_y*np.sin(theta),-1,1)
    # Spectral dispersion, continuously periodic instead of cycling solid body tints.
    hue=pane*.13+phase
    spectrum=np.stack([.55+.45*np.cos(2*np.pi*(hue-shift)) for shift in [0,1/3,2/3]],axis=2)
    white=np.clip((facing-.58)/.42,0,1)**4
    sweep=np.clip(np.cos((u*.55+v*.32)*2.2-theta)-.86,0,1)/.14
    rim=np.clip(2.5-distance,0,1)*(.3+.7*np.clip(nx*np.cos(theta)+ny*np.sin(theta),0,1))
    panes=np.where(((u%1)<.1)|((v%1)<.1)|(abs((u%1)+(v%1)-1)<.1),.08,0)
    rgb=a[:,:,:3].astype(float)/255
    luminance=rgb.mean(axis=2)
    # Preserve dark outlines/eyes: no wholesale white painting of facial features.
    protect=np.clip((luminance-.06)/.30,0,1)
    weight=(.07+.11*(facing+1)/2+panes)*protect
    # Small in-silhouette refraction; never samples background or another cell.
    dx=np.rint(normal_x*np.sin(theta)).astype(int)
    dy=np.rint(normal_y*np.cos(theta)).astype(int)
    sx=np.clip(xx+dx,0,a.shape[1]-1);sy=np.clip(yy+dy,0,a.shape[0]-1)
    refracted=rgb[sy,sx];valid=mask[sy,sx]&mask
    mixed=np.where(valid[:,:,None],rgb*.88+refracted*.12,rgb)
    mixed=mixed*(1-weight[:,:,None])+spectrum*weight[:,:,None]
    spec=np.clip((white*.56+sweep*.38+rim*.32)*protect,0,.83)
    glint=.76+.24*spectrum
    result=mixed*(1-spec[:,:,None])+glint*spec[:,:,None]
    out=a.copy();out[:,:,:3]=np.uint8(np.clip(np.rint(result*255),0,255))
    # Transparent RGB is kept too, not merely the visible silhouette.
    out[~mask]=a[~mask]
    assert np.array_equal(out[:,:,3],a[:,:,3])
    return Image.fromarray(out)

def sheet(image,cell_size,phase):
    w,h=cell_size
    if w<=0 or h<=0 or image.width%w or image.height%h:raise ValueError('Invalid native sheet/cell geometry')
    out=Image.new('RGBA',image.size)
    for y in range(0,image.height,h):
        for x in range(0,image.width,w):
            out.paste(glass(image.crop((x,y,x+w,y+h)),phase),(x,y))
    return out
