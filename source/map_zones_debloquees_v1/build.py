from pathlib import Path
import json, hashlib, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "map_zones_debloquees_v1"
LAYERS = ROOT / "renders" / "cafe_multietage_v3" / "calques_alignés"
REFS = ROOT / "source" / "cafe_multietage_v3" / "references"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "layers").mkdir(exist_ok=True)
(OUT / "animations").mkdir(exist_ok=True)
(OUT / "sprites").mkdir(exist_ok=True)

W, H = 1600, 1000
SIZE = (W, H)

def rgba(path):
    return Image.open(path).convert("RGBA")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# The cafe's last-commit layered floor/walls are reused as the in-game hub.
room = rgba(LAYERS / "00_salle_vide.png")
room = room.resize((1264, 843), Image.Resampling.NEAREST)
background = Image.new("RGBA", SIZE, (28, 22, 18, 255))
background.alpha_composite(room, ((W-room.width)//2, 112))
# A subtle dark translucent frame separates the map from the furniture, without baking a character.
frame = Image.new("RGBA", SIZE, (0, 0, 0, 0)); d = ImageDraw.Draw(frame)
d.rounded_rectangle((270, 220, 1330, 850), radius=34, fill=(35, 25, 18, 225), outline=(188, 137, 73, 255), width=8)
d.rounded_rectangle((300, 250, 1300, 820), radius=24, fill=(227, 188, 111, 255), outline=(92, 57, 30, 255), width=5)
background.alpha_composite(frame)
fond_layer = background.copy()

# Canonical-guided map paper: palette comes from the native cafe floor/reference, no recolor of source pixels.
paper = Image.new("RGBA", SIZE, (0,0,0,0)); d = ImageDraw.Draw(paper)
d.rounded_rectangle((330, 280, 1270, 790), radius=18, fill=(238, 207, 139, 255), outline=(119, 76, 35, 255), width=4)
for y in range(300, 790, 24):
    d.line((345, y, 1255, y), fill=(190, 142, 77, 38), width=2)
paper = paper.filter(ImageFilter.GaussianBlur(0.15))
background.alpha_composite(paper)

# Paths are separate from the unlock state so the same map can be updated in game.
paths = Image.new("RGBA", SIZE, (0,0,0,0)); d = ImageDraw.Draw(paths)
points = {
    "accueil": (800, 700), "foret": (510, 590), "plage": (625, 420),
    "volcan": (810, 355), "desert": (1030, 410), "glace": (1130, 590),
    "tour": (850, 570),
}
route = [(points["accueil"], points["foret"]), (points["foret"], points["plage"]),
         (points["plage"], points["volcan"]), (points["volcan"], points["desert"]),
         (points["desert"], points["glace"]), (points["glace"], points["tour"]),
         (points["tour"], points["accueil"])]
for a,b in route:
    d.line((a,b), fill=(107, 67, 34, 150), width=15)
    d.line((a,b), fill=(247, 220, 157, 255), width=5)
background.alpha_composite(paths)

# New place emblems: intentionally new map markers, using the cafe's wood/cream visual language.
places = [
    ("foret", "Forêt", "F", True, (510,590), (74,119,69)),
    ("plage", "Plage", "≈", True, (625,420), (66,137,166)),
    ("volcan", "Volcan", "△", True, (810,355), (177,74,43)),
    ("desert", "Désert", "☼", False, (1030,410), (194,142,59)),
    ("glace", "Glace", "✧", False, (1130,590), (94,153,190)),
    ("tour", "Tour", "T", False, (850,570), (111,77,139)),
]
label_font, small_font = font(24), font(16)

def emblem_sprite(key, label, glyph, color, unlocked, pulse=0):
    im = Image.new("RGBA", (144, 144), (0,0,0,0)); q = ImageDraw.Draw(im)
    q.ellipse((8,8,136,136), fill=(57,39,25,255), outline=(232,194,113,255), width=6)
    q.ellipse((20,20,124,124), fill=(*color,255) if unlocked else (78,69,60,255), outline=(246,221,160,255), width=4)
    if unlocked:
        q.ellipse((28-pulse,28-pulse,116+pulse,116+pulse), outline=(255,240,176,95), width=3)
    q.text((72, 65), glyph, anchor="mm", font=font(42), fill=(255,244,204,255) if unlocked else (159,151,139,255), stroke_width=1)
    q.text((72, 128), "OK" if unlocked else "LOCK", anchor="mm", font=font(13), fill=(255,232,172,255) if unlocked else (181,173,163,255))
    return im

emblem_layer = Image.new("RGBA", SIZE, (0,0,0,0)); status_layer = Image.new("RGBA", SIZE, (0,0,0,0))
for key, label, glyph, unlocked, (x,y), color in places:
    icon = emblem_sprite(key, label, glyph, color, unlocked)
    emblem_layer.alpha_composite(icon, (x-72,y-72))
    dd = ImageDraw.Draw(status_layer)
    dd.text((x, y+88), label, anchor="mm", font=label_font, fill=(77,47,23,255))
    # The state stays on its own layer: a green/amber status pip avoids text collisions between nodes.
    pip = (54, 128, 67, 255) if unlocked else (126, 93, 55, 255)
    dd.ellipse((x+57, y-7, x+71, y+7), fill=pip, outline=(246,221,160,255), width=2)
dd.text((800, 300), "CARTE DES ZONES", anchor="mm", font=font(22), fill=(92,55,27,255))
background.alpha_composite(emblem_layer)
background.alpha_composite(status_layer)
background.save(OUT / "MapZones_debloquees.png")

# Export five semantic layers. The animated glow is not baked into the emblem layer.
layer_data = {
    "00_fond_hub_cafe.png": fond_layer,
    "01_carte_parchemin.png": paper,
    "02_chemins_zones.png": paths,
    "03_emblemes_lieux.png": emblem_layer,
    "04_etat_zones_debloquees.png": status_layer,
}
for name, im in layer_data.items():
    im.save(OUT / "layers" / name)

# Animation: genuine independent PNG frames and a WebP loop, with only unlocked nodes pulsing.
frames=[]
for i in range(8):
    frame = Image.new("RGBA", SIZE, (0,0,0,0))
    glow = Image.new("RGBA", SIZE, (0,0,0,0)); gd=ImageDraw.Draw(glow)
    pulse = int(4 + 3 * (1 + math.sin(i*math.pi/4))/2)
    for key, label, glyph, unlocked, (x,y), color in places:
        if unlocked:
            gd.ellipse((x-65-pulse,y-65-pulse,x+65+pulse,y+65+pulse), outline=(255,237,154,130), width=5)
            gd.ellipse((x-73-pulse,y-73-pulse,x+73+pulse,y+73+pulse), outline=(255,204,88,60), width=3)
    frame.alpha_composite(glow)
    out = background.copy(); out.alpha_composite(frame)
    frames.append(out)
    out.save(OUT / "animations" / f"MapZones_unlock_{i:02d}.png")
frames[0].save(OUT / "animations" / "MapZones_unlock.webp", save_all=True, append_images=frames[1:], duration=125, loop=0, lossless=True)

# One compact asset-sprite sheet plus metadata for engine/UI integration.
sheet = Image.new("RGBA", (6*144, 144), (0,0,0,0))
asset_entries=[]
for i,(key,label,glyph,unlocked,pos,color) in enumerate(places):
    icon=emblem_sprite(key,label,glyph,color,unlocked)
    sheet.alpha_composite(icon,(i*144,0))
    asset_entries.append({"id":key,"label":label,"rect":[i*144,0,144,144],"unlocked_by_default":unlocked})
sheet.save(OUT / "ZoneEmblemes_AssetSprite.png")
(OUT / "assetsprite.json").write_text(json.dumps({"format":"AssetSprite","sheet":"ZoneEmblemes_AssetSprite.png","frame_size":[144,144],"entries":asset_entries}, ensure_ascii=False, indent=2))

manifest={
    "name":"Map Zones Débloquées — Café",
    "canvas_px":[W,H], "semantic_layers":list(layer_data),
    "animated_frames":8, "animation":"animations/MapZones_unlock.webp",
    "asset_sprite":"ZoneEmblemes_AssetSprite.png",
    "sources":{
        "generated_last_commit_layers":"renders/cafe_multietage_v3/calques_alignés/00_salle_vide.png and aligned layers",
        "canonical_floor_reference":"source/cafe_multietage_v3/references/Guild_Second_Floor_Floor.tile",
        "canonical_wall_reference":"source/cafe_multietage_v3/references/Guild_Second_Floor_Walls.tile",
        "canonical_render_reference":"source/cafe_multietage_v3/references/guild_second_floor_reference.png"
    },
    "notes":"Les six emblemes sont de nouveaux marqueurs de carte, non des sprites Pokémon. L'etat deblocage et l'animation restent sur des calques independants. Le sol et les murs reprennent le langage cafe du dernier commit; les fichiers natifs restent inchanges."
}
for p in [*OUT.rglob('*.png'),*OUT.rglob('*.webp'),OUT/'assetsprite.json']:
    manifest.setdefault('files',{})[str(p.relative_to(OUT))] = {"sha256":sha(p),"bytes":p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(f"Built {len(layer_data)} layers, {len(frames)} animation frames and {len(places)} emblems")
