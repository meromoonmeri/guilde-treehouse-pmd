"""Assemble a separate 0.8.12 editing project, with its COMPLETE native index.
The merged-install option explicitly skips copying that index into another mod.
"""
from pathlib import Path
import importlib.util
import shutil
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PACK=Path.home()/'.cache/cote_v3_0812_pack'
NAMESPACE='cotes_v2_0812'


def main():
    spec=importlib.util.spec_from_file_location('index_tools',ROOT/'source/pmdo_cote/INSTALLER.py')
    tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
    nodes={}
    for path in sorted((PACK/'Content/Tile').glob('*.tile')):
        with path.open('rb') as f:nodes[path.stem]=tools.read_node(f)
    assert len(nodes)==4
    (PACK/'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/meromoonmeri/guilde-treehouse-pmd/cotes_v2_0812')
    (PACK/'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Cotes V2 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : 10 terrains V2, roche Metano native, jour et nuit. Pas une aventure jouable.</Description>
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
    print('Separate editing project: Mod.xml, complete 4-sheet index, 20 namespaced map scripts.')


if __name__=='__main__':main()
