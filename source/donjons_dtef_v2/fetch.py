from pathlib import Path
import subprocess,concurrent.futures,json
P=Path(__file__).parent/'references';pin='1522c7a8b7a34d70078e11ed605b21d563b0dc51'
paths=['Data/Zone/relic_forest.json','Data/Zone/illuminant_riverbed.json','Data/Script/halcyon/zone/relic_forest/init.lua','Data/Script/halcyon/zone/illuminant_riverbed/init.lua','Content/Tile/Relic_Forest_Base.tile','Content/Tile/Illuminant_Riverbed_Base.tile']
def get(path):
 dest=P/path;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():dest.write_bytes(subprocess.check_output(['gh','api',f'repos/Palikadude/Halcyon/contents/{path}?ref={pin}','-H','Accept: application/vnd.github.raw+json']))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(get,paths))
