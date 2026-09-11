"""Vérification indépendante des PNG, cels Aseprite et tuiles animées Tiled."""
from pathlib import Path
from PIL import Image
import json
import numpy as np
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]


def image(path):
    with Image.open(path) as im:
        assert im.mode == 'RGBA', (path, 'Calque non RGBA')
        return im.copy()


def equal(a, b, message):
    assert np.array_equal(np.array(a), np.array(b)), message


def samples(count):
    return [0, 1, 6, 12, 23, 24, count//2, count-2, count-1]


class ReferenceLayer:
    """Recompose à partir des données publiques, sans appeler le reconstructeur."""
    def __init__(self, im, spec, root):
        self.array = np.array(im)
        self.spec = spec
        self.period = spec['period'] if spec else 1
        self.cache = {}
        self.groups = np.array(Image.open(root / spec['groups'])).astype(int) if spec and spec['kind'] == 'stars' else None
        self.source_atlas = image(root / spec['source_atlas']) if spec and spec['kind'] == 'frames' else None
        self.indices = np.array(Image.open(root / spec['indices'])).astype(int) if spec and spec['kind'] == 'palette_cycle' else None

    def at(self, frame):
        phase = frame % self.period
        if phase in self.cache:
            return self.cache[phase]
        a = self.array.copy()
        if self.spec:
            kind = self.spec['kind']
            if kind == 'scroll':
                a = np.roll(a, -phase*self.spec.get('step',1), axis=1)
            elif kind == 'stars':
                factors = np.array(self.spec['levels'][phase], dtype=np.uint32)[self.groups]
                a[:, :, 3] = ((a[:, :, 3].astype(np.uint32)*factors+127)//255).astype('uint8')
            elif kind == 'palette_cycle':
                a = np.asarray(self.spec['palettes'][phase], dtype=np.uint8)[self.indices]
            elif kind == 'frames':
                w, h = self.spec['source_frame_size']
                col, row = phase % self.spec['source_columns'], phase//self.spec['source_columns']
                a = np.array(self.source_atlas.crop((col*w, row*h, (col+1)*w, (row+1)*h)))
            elif kind == 'waves':
                dx, dy, alpha = self.spec['phases'][phase]
                a = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
                a[:, :, 3] = ((a[:, :, 3].astype(np.uint32)*alpha+127)//255).astype('uint8')
            else:
                raise AssertionError(kind)
        a[a[:, :, 3] == 0] = 0
        q = Image.fromarray(a)
        if self.period <= 48:
            self.cache[phase] = q
        return q


def references(root, manifest, mode):
    f = manifest['fichiers'][mode]
    return [ReferenceLayer(image(root / f['calques'][l['id']]), f['operations'].get(l['id']), root) for l in manifest['calques']]


def expected(refs, frame, size, excluded=None, base_start=0):
    out = Image.new('RGBA', size)
    for i, layer in enumerate(refs):
        if i >= base_start and i != excluded:
            out.alpha_composite(layer.at(frame))
    return out


def verify_ase(path, refs, size, count, duration):
    raw = path.read_bytes()
    header = struct.unpack_from('<IHHHHHIH', raw)
    assert header == (len(raw), 0xA5E0, count, *size, 32, 1, duration)
    assert struct.unpack_from('<hhHH', raw, 36) == (0, 0, 8, 8)
    pos, definitions, history, tags = 128, 0, {}, []
    for frame in range(count):
        frame_size, magic, chunks, time = struct.unpack_from('<IHHH', raw, pos)
        assert magic == 0xF1FA and time == duration
        end, p, cels = pos+frame_size, pos+16, {}
        for _ in range(chunks):
            length, kind = struct.unpack_from('<IH', raw, p)
            assert length >= 6 and p+length <= end
            d = raw[p+6:p+length]
            if kind == 0x2004:
                assert frame == 0
                definitions += 1
            elif kind == 0x2018:
                assert struct.unpack_from('<H', d)[0] == 1
                tags.append(struct.unpack_from('<HHB', d, 10))
            elif kind == 0x2005:
                i, x, y, opacity, typ, z = struct.unpack_from('<HhhBHh', d)
                assert i not in cels and 0 <= i < len(refs) and opacity == 255 and z == 0
                if typ == 2:
                    w, h = struct.unpack_from('<HH', d, 16)
                    q = Image.frombytes('RGBA', (w, h), zlib.decompress(d[20:]))
                    target = refs[i].at(frame)
                    box = target.getbbox()
                    if refs[i].spec and refs[i].spec.get('ase_linked_motion'):
                        assert frame==0 and refs[i].spec['kind']=='scroll'
                        band=target.crop((0,box[1],size[0],box[3]));cropped=Image.new('RGBA',(size[0]*2,band.height))
                        cropped.paste(band,(0,0));cropped.paste(band,(size[0],0));xy=(0,box[1])
                    else:
                        xy = box[:2] if box else (0, 0)
                        cropped = target.crop(box) if box else Image.new('RGBA', (1, 1))
                    assert (x, y) == xy, (path, frame, i, 'Position du cel')
                    equal(q, cropped, (path, frame, i, 'Pixels du cel'))
                else:
                    assert typ == 1
                    linked = struct.unpack_from('<H', d, 16)[0]
                    assert linked < frame
                    sx, sy, q = history[linked, i]
                    if refs[i].spec and refs[i].spec.get('ase_linked_motion'):
                        assert linked==0 and (x,y)==(-(frame%refs[i].period)*refs[i].spec.get('step',1),sy)
                    else:
                        assert linked==frame%refs[i].period
                        assert (x, y) == (sx, sy), (path, frame, i, 'Cel lié déplacé')
                cels[i] = (x, y, q)
                history[frame, i] = cels[i]
            p += length
        assert p == end and set(cels) == set(range(len(refs)))
        if frame in samples(count):
            im = Image.new('RGBA', size)
            for i in range(len(refs)):
                x, y, q = cels[i]
                im.alpha_composite(q, (x, y))
            equal(im, expected(refs, frame, size), (path, frame, 'Composition'))
        pos = end
    assert pos == len(raw) and definitions == len(refs) and tags == [(0, count-1, 0)]


def verify_tiled(path, refs, size, count, duration):
    tm = json.loads(path.read_text(encoding='utf-8'))
    assert (tm['width']*tm['tilewidth'], tm['height']*tm['tileheight']) == size
    assert tm['tilewidth'] == tm['tileheight'] == 8 and tm['orientation'] == 'orthogonal'
    assert len(tm['layers']) == len(refs)+1 and not tm['layers'][-1]['visible']
    render_sources = []
    for i, (layer, ref) in enumerate(zip(tm['layers'], refs)):
        if not ref.spec:
            assert layer['type'] == 'imagelayer'
            q = image((path.parent / layer['image']).resolve())
            equal(q, ref.at(0), (path, i, 'Calque fixe'))
            render_sources.append((q, 0, None))
            continue
        assert layer['type'] == 'objectgroup' and len(layer['objects']) == 1
        obj = layer['objects'][0]
        ts = next(t for t in tm['tilesets'] if t['firstgid'] == obj['gid'])
        assert ts['objectalignment'] == 'bottomleft' and ts['tilecount'] == ref.period
        assert ts['tiles'][0]['animation'] == [{'tileid': f, 'duration': duration} for f in range(ref.period)]
        atlas = image((path.parent / ts['image']).resolve())
        assert atlas.size == (ts['imagewidth'], ts['imageheight'])
        w, h = ts['tilewidth'], ts['tileheight']
        assert w == size[0] and obj['x'] == 0 and obj['width'] == w and obj['height'] == h
        y = obj['y']-h
        for f in range(ref.period):
            ax, ay = (f % ts['columns'])*w, (f//ts['columns'])*h
            tile = atlas.crop((ax, ay, ax+w, ay+h))
            target = ref.at(f)
            equal(tile, target.crop((0, y, w, y+h)), (path, i, f, 'Tuile animée'))
            assert not np.array(target)[:y, :, 3].any() and not np.array(target)[y+h:, :, 3].any()
        assert count % ref.period == 0
        render_sources.append((atlas, y, ts))
    for f in samples(count):
        im = Image.new('RGBA', size)
        for i, (source, y, ts) in enumerate(render_sources):
            if ts:
                phase = f % refs[i].period
                w, h = ts['tilewidth'], ts['tileheight']
                x, ay = (phase % ts['columns'])*w, (phase//ts['columns'])*h
                q = source.crop((x, ay, x+w, ay+h))
            else:
                q = source
            im.alpha_composite(q, (0, y))
        equal(im, expected(refs, f, size), (path, f, 'Composition Tiled'))


def verify_border_tileset(root, files, mode):
    info = files['tileset_bordures']
    assert info['tile_size'] == 24 and info['count'] == 20
    atlas = image(root / info['png'])
    assert atlas.size == (120, 96)
    ts_path = root / info['tiled']
    ts = json.loads(ts_path.read_text(encoding='utf-8'))
    assert (ts['tilewidth'], ts['tileheight'], ts['columns'], ts['tilecount']) == (24, 24, 5, 20)
    equal(image((ts_path.parent / ts['image']).resolve()), atlas, 'Image du tileset incorrecte')
    assert [tile['id'] for tile in ts['tiles']] == list(range(20))
    definitions = json.loads((ROOT / 'source/bordures_pmd/definitions.json').read_text(encoding='utf-8'))
    for family in ['rive', 'angle_sortant', 'angle_rentrant', 'diagonale', 'paroi']:
        assert sum(t['famille'] == family for t in definitions['motifs']) == 4
    for i, item in enumerate(definitions['motifs']):
        props = {p['name']: p['value'] for p in ts['tiles'][i]['properties']}
        assert props['motif'] == item['id_motif'] and props['orientation'] == item['orientation']
        assert atlas.crop(((i % 5)*24, (i//5)*24, (i % 5+1)*24, (i//5+1)*24)).getbbox()
    catalogue_path = root / info['catalogue']
    catalogue = json.loads(catalogue_path.read_text(encoding='utf-8'))
    assert catalogue['tilewidth'] == catalogue['tileheight'] == 24
    assert catalogue['layers'][0]['data'] == list(range(1, 21))
    assert (catalogue_path.parent / catalogue['tilesets'][0]['source']).resolve() == ts_path.resolve()
    scene = json.loads((root / files['tiled']).read_text(encoding='utf-8'))
    assert any(t.get('source') == ts_path.name for t in scene['tilesets']), 'Tileset absent de la palette Tiled'
    source_alpha = np.array(image(ROOT / 'source/bordures_pmd/bordures_redessinees.png'))[:, :, 3]
    assert np.array_equal(np.array(atlas)[:, :, 3], source_alpha)


def verify_scene(scene):
    root = ROOT / scene
    m = json.loads((root / 'kit.json').read_text(encoding='utf-8'))
    size = tuple(m['dimensions'])
    count, duration = m['animation']['frames'], m['animation']['duree_image_ms']
    assert count % size[0] == 0 and duration == 250
    assert all(v % 8 == 0 for v in size)
    source = ROOT / 'source' / scene
    mask = np.array(Image.open(source / 'masque_harmonisation_sol.png'))
    original_name = 'falaise_avant_harmonisation.png' if scene == 'falaise' else 'falaise_avant_prairie.png'
    original = np.array(image(source / original_name))
    native = np.array(image(source / 'falaise_native.png'))
    surface = np.array(Image.open(source / 'masque_sommet.png')) > 0
    generated = np.array(image(source / 'sommet_genere.png'))
    border_mask = np.zeros(size[::-1], dtype=np.uint8)
    if scene == 'sharpedo':
        border_mask = np.array(Image.open(source / 'masque_bordures_pmd.png'))
    unchanged = border_mask == 0
    entire_eos = scene == 'falaise' and bool(m['regles'].get('passe_eos_entiere'))
    if entire_eos:
        eos = np.array(image(source / 'falaise_eos_generee.png'))
        protected_stairs = np.zeros(size[::-1], dtype=bool)
        protected_stairs[328:408, 196:284] = True
        assert np.array_equal(native[~protected_stairs], eos[~protected_stairs]), 'Reprise entière EoS absente'
    else:
        assert np.array_equal(native[surface & unchanged], generated[surface & unchanged]), 'Intérieur de prairie modifié'
    if scene == 'falaise':
        if not entire_eos:
            assert np.array_equal(native[mask == 0], original[mask == 0]), 'Hors retouche modifié'
        assert np.array_equal(native[:, :, 3], original[:, :, 3]), 'Contour modifié'
    else:
        wall_mask = np.array(Image.open(source / 'masque_paroi_naturelle.png'))
        before_wall = np.array(image(source / 'falaise_avant_paroi_naturelle.png'))
        new_wall = np.array(image(source / 'paroi_naturelle_generee.png'))
        assert not wall_mask[surface].any()
        assert np.array_equal(native[(wall_mask == 0) & unchanged], before_wall[(wall_mask == 0) & unchanged]), 'Prairie ou chemin altéré'
        assert np.array_equal(native[(wall_mask == 255) & unchanged], new_wall[(wall_mask == 255) & unchanged]), 'Nouvelle paroi absente'
        assert np.count_nonzero(native[:, :, 3] != before_wall[:, :, 3]) > 500, 'Ancien profil conservé'
        before_borders = np.array(image(source / 'falaise_avant_bordures_pmd.png'))
        border_art = np.array(image(source / 'bordures_layout_generees.png'))
        path_mask = np.array(Image.open(source / 'masque_chemin_protege.png')) > 0
        assert np.array_equal(native[unchanged], before_borders[unchanged]), 'Hors bordure modifié'
        assert np.array_equal(native[:, :, 3], before_borders[:, :, 3]), 'Emprise modifiée par les bordures'
        assert np.array_equal(native[path_mask], before_borders[path_mask]), 'Chemin modifié'
        assert not border_mask[145:211, 480:].any(), 'Sortie droite fermée'
        assert not border_mask[300:, 450:].any(), 'Bordure artificielle en limite droite/basse'
        full_border = border_mask == 255
        assert np.array_equal(native[full_border, :3], border_art[full_border, :3])
        assert np.count_nonzero(np.any(native != before_borders, axis=2)) > 2000, 'Retouche de bordures absente'
    report = {'scene': scene, 'dimensions': list(size), 'calques': len(m['calques']), 'frames_par_ambiance': count,
              'sommet_entierement_genere': True, 'pixels_sommet': int(surface.sum()),
              'contour_et_paroi_hors_raccord_conserves': True, 'ambiances': [], 'inspection_artistique_automatisee': False}
    if entire_eos:
        report.pop('contour_et_paroi_hors_raccord_conserves')
        report['passe_complete_eos'] = True
        report['emprise_reference_conservee'] = True
    if scene == 'sharpedo':
        report.pop('contour_et_paroi_hors_raccord_conserves')
        report['prairie_interieure_chemin_conserves'] = True
        report['bordures_pmd_redessinees'] = True
        report['motifs_bordures'] = 20
        report['sorties_droite_basse_ouvertes'] = True
        report['paroi_naturelle_remplacee'] = True
        report['silhouette_inferieure_actualisee'] = True
    for mode in m['ambiances']:
        refs = references(root, m, mode)
        f = m['fichiers'][mode]
        assert all(ref.array.shape == (*size[::-1], 4) for ref in refs)
        equal(expected(refs, 0, size), image(root / f['composition']), (scene, mode, 'PNG composé'))
        base = expected(refs, 0, size, base_start=m['base_start'])
        equal(base, image(root / f['base']), (scene, mode, 'Base'))
        mag = Image.new('RGBA', size, (255, 0, 255, 255))
        mag.alpha_composite(base)
        equal(mag, image(root / f['magenta']), (scene, mode, 'Magenta'))
        for ref in refs:
            equal(ref.at(0), ref.at(count), (scene, mode, 'Raccord cyclique'))
            if ref.spec and ref.spec['kind'] == 'stars':
                moon = (ref.groups == 0) & (ref.array[:, :, 3] > 0)
                assert moon.any()
                assert not np.array_equal(np.array(ref.at(0)), np.array(ref.at(6))), 'Étoiles immobiles'
                for frame in range(24):
                    assert np.array_equal(np.array(ref.at(frame))[moon], ref.array[moon]), 'La lune clignote'
            if ref.spec and ref.spec['kind'] in ['waves', 'frames']:
                assert not np.array_equal(np.array(ref.at(0)), np.array(ref.at(6))), 'Mer immobile'
                if scene == 'sharpedo':
                    assert ref.spec['kind'] == 'frames' and ref.period == 10
                    assert len({ref.at(f).tobytes() for f in range(10)}) == 10, 'Phases de mer dupliquées'
        if scene == 'falaise' and mode == 'jour':
            equal(refs[4].at(0).crop((196, 328, 284, 408)), image(source / 'reference_escalier.png'), 'Escalier altéré')
            r, g, b = [native[:, :, i].astype(int) for i in range(3)]
            green = (g > r+8) & (g > b+15)
            assert green[surface].mean() > .4 and green[320:328, 224:256].mean() < .2
        verify_ase(root / f['aseprite'], refs, size, count, duration)
        verify_tiled(root / f['tiled'], refs, size, count, duration)
        if scene == 'sharpedo':
            verify_border_tileset(root, f, mode)
        report['ambiances'].append({'id': mode, 'PNG_Aseprite_Tiled': 'identiques', 'frames_verifiees': count,
                                    'animations': [v['kind'] for v in f['operations'].values()], 'terrain_fixe': True})
        print('PASS', scene, mode, '—', count, 'frames ; PNG/Aseprite/Tiled identiques', flush=True)
    report['frames_verifiees_par_format'] = count*len(m['ambiances'])
    report['etoiles_scintillantes_lune_fixe'] = True
    report['escalier_reference_identique_jour'] = scene == 'falaise'
    report['mer_overlay_anime'] = scene == 'sharpedo'
    if scene == 'sharpedo':
        report['cycle_mer_reference_10_phases'] = True
    (root / 'controle_qualite.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def verify():
    return [verify_scene(name) for name in ['falaise', 'sharpedo']]


if __name__ == '__main__':
    verify()
