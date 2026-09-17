# Terapagos / Terrapagos #1024 — portraits PMD / SpriteCollab

Ce pack complète les portraits SpriteCollab de Terapagos sans mélanger ses
formes. Les trois variantes canoniques restent dans leurs chemins respectifs :

- `portrait/1024/0000/0001/` — Normal Form ;
- `portrait/1024/0001/` — Terastal Form ;
- `portrait/1024/0002/` — Stellar Form.

Chaque variante contient 20 expressions normales, 20 variantes miroir et une
planche SpriteBot `Sheet.png` de 200×320 px. Les portraits individuels restent
à leur taille native 40×40 et utilisent au maximum 15 couleurs.

## Méthode

`build_portraits.py` travaille depuis les références canoniques enregistrées
dans `reference/` :

1. les PNG upstream déjà publiés sont copiés byte-for-byte ;
2. les expressions manquantes sont dessinées pixel par pixel sur le `Normal`
   de la même forme, sans emprunter de pixels à une autre forme ;
3. les expressions miroir nouvellement créées sont des retournements exacts ;
4. les planches et archives sont reconstruites de manière déterministe ;
5. aucune sortie générée par IA brute n'est livrée comme portrait final.

Les fichiers canoniques sont épinglés au commit SpriteCollab
`8f85c1a6556a7ac61fe8987f88da3415cfffb782`.

## Archives

- `portrait-1024-0000-0001.zip` — Normal Form ;
- `portrait-1024-0001.zip` — Terastal Form ;
- `portrait-1024-0002.zip` — Stellar Form ;
- `portrait-1024.zip` — archive agrégée contenant les trois chemins de variantes.

## Contrôle et reproduction

```bash
python source/portraits_terapagos/build_portraits.py
python source/portraits_terapagos/verify_portraits.py
```

Le vérificateur confirme les 120 portraits, les dimensions, les palettes, les
copies canoniques, les miroirs, les planches et les quatre archives.
