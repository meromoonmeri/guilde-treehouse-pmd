"""Produit le test de personnalité autonome, sans dépendance réseau à l'exécution."""
from pathlib import Path
import base64
import json

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / 'source/reve'


def data_uri(path, mime):
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()


def build():
    manifest = json.loads((ROOT / 'reve/kit.json').read_text(encoding='utf-8'))
    data = {'manifest': manifest,
            'questions': json.loads((S / 'questions.json').read_text(encoding='utf-8')),
            'natures': json.loads((S / 'natures.json').read_text(encoding='utf-8'))['natures'],
            'assets': {'nebuleuse': data_uri(ROOT / 'reve/assets/nebuleuse.webp', 'image/webp'),
                       'anneaux': data_uri(ROOT / 'reve/assets/anneaux_36_phases.png', 'image/png')}}
    html = (S / 'page.html').read_text(encoding='utf-8')
    html = html.replace('__CSS__', (S / 'style.css').read_text(encoding='utf-8'))
    html = html.replace('__BUNDLE__', (ROOT / 'reve/reve.bundle.js').read_text(encoding='utf-8'))
    html = html.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    target = ROOT / 'apercu_reve.html'
    temporary = target.with_suffix('.html.tmp')
    temporary.write_text(html, encoding='utf-8')
    temporary.replace(target)
    print('Rêve autonome :', target.stat().st_size, 'octets ; aucun CDN ni service extérieur.')


if __name__ == '__main__':
    build()
