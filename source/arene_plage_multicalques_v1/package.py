import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = ROOT / 'exports/arene_plage_multicalques_v1'
RENDERS_DIR = ROOT / 'renders/arene_plage_multicalques_v1'
zip_path = ROOT / 'exports/arene_plage_multicalques_v1_pack.zip'

def main():
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for p in EXPORTS_DIR.rglob('*'):
            if p.is_file():
                zf.write(p, 'exports/' + str(p.relative_to(EXPORTS_DIR)))
        for p in RENDERS_DIR.rglob('*'):
            if p.is_file():
                zf.write(p, 'renders/' + str(p.relative_to(RENDERS_DIR)))
    print(f"Pack created: {zip_path} ({zip_path.stat().st_size} bytes)")

if __name__ == '__main__':
    main()
