import zipfile
from pathlib import Path

R = Path(__file__).resolve().parents[2]
O = R / 'exports/zones_rock_layouts_v1'
zip_path = R / 'exports/zones_rock_layouts_v1_pack.zip'

def main():
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for p in O.rglob('*'):
            if p.is_file():
                arcname = p.relative_to(O.parent)
                zf.write(p, arcname)
    print(f"Pack created: {zip_path} ({zip_path.stat().st_size} bytes)")

if __name__ == '__main__':
    main()
