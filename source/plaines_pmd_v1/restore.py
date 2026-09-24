"""Pinned wild plains: --restore; --build --verify; --serve (8016)."""
import subprocess
from pathlib import Path
REV='93914f687cc3e3e40ae0b57a38599e7281b71b22'
exec(compile(subprocess.check_output(["git","show",REV+":source/plaines_pmd_v1/work.py"],cwd=Path(__file__).resolve().parents[2]),__file__,"exec"))
