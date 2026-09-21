"""Safe graphics/Ground installation; Halcyon boss is explicit opt-in.
Close PMDO and back up the mod first. Uses the existing lossless tile-index merger.
"""
from pathlib import Path
import argparse,shutil,tempfile,xml.etree.ElementTree as ET
from install_base import install
S=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('mod',type=Path);p.add_argument('--dry-run',action='store_true');p.add_argument('--halcyon-boss',action='store_true');a=p.parse_args();target=a.mod.resolve()
 if not (target/'Mod.xml').is_file():raise ValueError('Target must be a mod containing Mod.xml')
 ns=ET.parse(target/'Mod.xml').getroot().findtext('Namespace');event=target/'Data/Script/halcyon/event.lua';line="require 'halcyon.ib1_ice'";before=None
 if a.halcyon_boss:
  if ns!='halcyon' or not event.is_file() or not (target/'Data/Map/searing_crucible.rsmap').is_file():raise ValueError('Boss integration requires a copy of Halcyon working-copy; no modification made')
  before=event.read_bytes()
 with tempfile.TemporaryDirectory(prefix='ib1_install_') as temp:
  stage=Path(temp)
  for top in ['Content','Data']:
   for src in (S/top).rglob('*'):
    if not src.is_file():continue
    rel=src.relative_to(S)
    if not a.halcyon_boss and (rel.parts[:2] in [('Data','Map'),('Data','Tile')] or rel.parts[:3]==('Data','Script','halcyon')):continue
    dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  install(stage,target,a.dry_run,ns)
 if a.halcyon_boss:
  if line.encode() not in before:
   if a.dry_run:print('Would append the IB1 module require to halcyon/event.lua (with backup)')
   else:
    backup=event.with_name('event.lua.ib1-backup')
    if not backup.exists():backup.write_bytes(before)
    event.write_bytes(before+b'\n-- IB1 isolated icy boss module\n'+line.encode()+b'\n')
  print('IMPORTANT: register/save ib1_ice_spikes in the PMDO Tile data editor and rebuild data indices before testing the dungeon maps. No engine validation or data-index binary generation is claimed.')
 print('Ground previews are static. The dungeon controller is turn-based. No original map replaced.')
if __name__=='__main__':main()
