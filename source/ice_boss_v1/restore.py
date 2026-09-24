"""IB1 pinned sources: --restore; --build --verify; --serve (8017)."""
import subprocess
from pathlib import Path
REV='8d7ca1d782a7a761d08d117412000bdccd7b22be'
exec(compile(subprocess.check_output(["git","show",REV+":source/ice_boss_v1/work.py"],cwd=Path(__file__).resolve().parents[2]),__file__,"exec"))
