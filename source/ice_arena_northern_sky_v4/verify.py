"""Independent output audit: original terrain, endpoints, relative viewer assets,
all decoded WebP frames and all recorded output hashes. No game/GPU execution.
"""
from pathlib import Path
import json, hashlib, re
from PIL import Image
R=Path(__file__).resolve().parents[2]
O=R/'renders/ice_arena_northern_sky_v4'
P='NorthernSkyV4'
def load(path):return Image.open(path).convert('RGBA')
def verify():
    old=R/'renders/ice_arena_aurora_coherent_v3/layers/IceAuroraCoherentV3_Terrain.png'
    assert old.read_bytes()==(O/'layers'/f'{P}_Terrain.png').read_bytes()
    terrain=load(old);sky=load(O/'layers'/f'{P}_Sky.png');strip=load(O/'layers'/f'{P}_CloudStrip.png')
    aurora=[load(O/'aurora_frames'/f'{P}_Aurora_{f:02}.png') for f in range(64)]
    stars=[load(O/'star_frames'/f'{P}_Stars_{f:02}.png') for f in range(64)]
    assert aurora[0].tobytes()==load(O/'keyframes'/f'{P}_Aurora_A.png').tobytes()
    assert aurora[32].tobytes()==load(O/'keyframes'/f'{P}_Aurora_B.png').tobytes()
    timeline=json.loads((O/'timeline.json').read_text());assert sum(r['ticks'] for r in timeline['samples'])==384
    paths=re.findall(r'"((?:aurora_frames|star_frames|layers)/[^" ]+\.png)"',(O/'index.html').read_text())
    assert len(paths)==131 and all((O/p).is_file() for p in paths)
    decoded=0
    for filename,count,moving,loop in [('composition_loop.webp',64,False,0),('composition_clouds_excerpt.webp',80,True,1)]:
        movie=Image.open(O/filename);assert movie.n_frames==count
        elapsed=0
        for f in range(count):
            expected=sky.copy();expected.alpha_composite(stars[f%64]);expected.alpha_composite(aurora[f%64])
            cloud=Image.new('RGBA',(512,288));offset=f//5 if moving else 0
            for x in range(-offset,512,1440):cloud.paste(strip,(x,0))
            expected.alpha_composite(cloud);expected.alpha_composite(terrain)
            movie.seek(f);movie.load()
            assert movie.convert('RGBA').tobytes()==expected.tobytes(),(filename,f)
            assert movie.info['duration']==100;elapsed+=movie.info['duration'];decoded+=1
        assert movie.info['loop']==loop and elapsed==count*100
    if (O/'files.sha256.json').is_file():
        for name,h in json.loads((O/'files.sha256.json').read_text()).items():
            assert hashlib.sha256((O/name).read_bytes()).hexdigest()==h,name
    print(f'PASS: unchanged terrain, both key poses, 131 viewer image paths, {decoded} decoded WebP frames and recorded hashes. No GPU test.')
if __name__=='__main__':verify()
