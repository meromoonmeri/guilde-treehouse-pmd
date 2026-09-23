"""Restore redundant V1 exports from the existing, preserved delivery archive."""
from pathlib import Path,PurePosixPath
import zipfile

def restore_exports(root):
    archive=root/'BeachNetwork_pack.zip'
    if not archive.exists():
        return 0  # A first build creates the files before its first packaging.
    count=0
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe archive member')
            if not ((path.suffix=='.png' and 'animation' in path.parts) or path.suffix=='.ora' or (path.name=='composition.png' and len(path.parts)==3)):
                continue
            dest=root/str(path)
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(z.read(name));count+=1
    return count

if __name__=='__main__':
    print('Restored',restore_exports(Path(__file__).resolve().parents[2]/'renders/beach_network_v1'),'exports')
