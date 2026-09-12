"""Run actual PMDO headlessly in the disposable cache installation.
Temporary Lua hook is restored even on failure. Never targets a user installation.
This validates Ground deserialization, NOT GPU assets or the graphical editor.
"""
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RUNTIME=ROOT/'.cache/pmdo-runtime/engine/PMDO'


def main():
    assert (RUNTIME/'PMDO').is_file(), 'Install pinned RUNTIMEPMDO archive in .cache first'
    assert (RUNTIME/'Base/PathParams.xml').is_file(), 'Install base assets first'
    with zipfile.ZipFile(ROOT/'cotes_metano_abyss_0812_pmdo.zip') as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        z.extractall(RUNTIME/'MODS')
    startup=RUNTIME/'Data/Script/origin/main.lua'
    original=startup.read_bytes()
    hook=(HERE/'test_ground_load.lua').read_bytes()
    assert b'NATIVE_GROUND_TEST' not in original, 'Restore original main.lua before rerunning'
    result_file=RUNTIME/'native_ground_test.tsv'
    if result_file.exists():result_file.unlink()
    try:
        startup.write_bytes(original+b'\n'+hook)
        process=subprocess.run(['./PMDO','-guide','-quest','cotes_metano_abyss_0812'],cwd=RUNTIME,
                               stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        (ROOT/'.cache/pmdo-runtime/ground-load.log').write_bytes(process.stdout)
        assert process.returncode==0,process.stdout.decode(errors='replace')
        rows=result_file.read_text().splitlines()
        assert len(rows)==20 and all(row.endswith('\tPASS') for row in rows)
        (HERE/'ground_load_results.tsv').write_text('\n'.join(rows)+'\n')
        print('PASS: 20 maps deserialized by actual PMDO 0.8.12. No graphics test.')
    finally:
        startup.write_bytes(original)
    assert startup.read_bytes()==original


if __name__=='__main__':main()
