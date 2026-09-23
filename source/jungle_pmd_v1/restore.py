"""Pinned jungle sources. --restore; --build --verify; --serve (8014)."""
import subprocess
from pathlib import Path
REV='6f3bc30d993721e1e7831468a33511ad0a596470'
exec(compile(subprocess.check_output(["git","show",REV+":source/jungle_pmd_v1/work.py"],cwd=Path(__file__).resolve().parents[2]),__file__,"exec"))
