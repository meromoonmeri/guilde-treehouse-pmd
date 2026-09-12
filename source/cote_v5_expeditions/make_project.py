"""Assemble a separate 0.8.12 editing project, with its COMPLETE native index.
The merged-install option explicitly skips copying that index into another mod.
"""
from pathlib import Path
import importlib.util
import shutil
import uuid
import zipfile
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACK=Path.home()/'.cache/cote_v5_expeditions_pack'
NAMESPACE='metano_expeditions'


def main():
    # Preserve previous Ground and resources byte-for-byte inside the new project.
    with zipfile.ZipFile(ROOT/'cotes_metano_abyss_0812_pmdo.zip') as archive:
        for name in archive.namelist():
            relative=name.split('/',1)[-1]
            if relative.startswith(('Data/Ground/','Data/Script/ground/','Content/')) and not relative.endswith('index.idx'):
                dest=PACK/relative;dest.parent.mkdir(parents=True,exist_ok=True)
                data=archive.read(name)
                if dest.exists():assert dest.read_bytes()==data
                else:dest.write_bytes(data)
    manifest=json.loads((ROOT/'sprites/cote_v5_expeditions/manifest.json').read_text())
    old=json.loads((ROOT/'sprites/cote_v4_abyss/manifest.json').read_text())
    for z in old['zones']:z['new']=False;z['kind']='archive';z['door']=None
    manifest['zones']+=old['zones']
    manifest['total_ground']=40
    (PACK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    spec=importlib.util.spec_from_file_location('index_tools',ROOT/'source/pmdo_cote/INSTALLER.py')
    tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
    nodes={}
    for path in sorted((PACK/'Content/Tile').glob('*.tile')):
        with path.open('rb') as f:nodes[path.stem]=tools.read_node(f)
    assert len(nodes)==8
    (PACK/'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/meromoonmeri/guilde-treehouse-pmd/metano_expeditions')
    (PACK/'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Metano Expeditions - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : 40 Ground dont 7 nouvelles falaises et 3 entrees, roche Metano native, jour et nuit. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    for source in (PACK/'Data/Script/ground').glob('*/init.lua'):
        target=PACK/'Data/Script'/NAMESPACE/'ground'/source.parent.name/'init.lua'
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    script=(ROOT/'source/pmdo_cote/INSTALLER.py').read_text()
    needle='            relative = src.relative_to(source)\n'
    assert needle in script
    script=script.replace(needle,needle+'''            # The delivered index belongs ONLY to this standalone project.
            # Merge its tile headers below; never overwrite another mod's index.
            if relative.as_posix() == 'Content/Tile/index.idx':
                continue
''')
    (PACK/'INSTALLER.py').write_text(script)
    assert len(list((PACK/'Data/Ground').glob('*.rsground')))==40
    print('Combined editing project: 40 Ground, 8 native tile banks, complete index.')


if __name__=='__main__':main()
