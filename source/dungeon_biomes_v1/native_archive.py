"""Lossless deduplication: native source bundle is already in the unchanged V1 ZIP."""
from pathlib import Path
import hashlib,zipfile
R=Path(__file__).resolve().parents[2]
SHA256="eae6a898c40d01d25fc71030ba26721be67caac98d066ac019d2840402403d30"
def native_source_archive():
 p=R/'.cache/redport_native_sources/native_sources.zip'
 if not p.exists():
  with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as z:raw=z.read('native_sources.zip')
  assert hashlib.sha256(raw).hexdigest()==SHA256
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA256
 return p
