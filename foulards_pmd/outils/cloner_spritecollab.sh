#!/usr/bin/env bash
# Clone partiel de SpriteCollab, limité aux 27 starters gen 1-3.
# Le dépôt complet pèse plusieurs Go ; ce clone-ci ~110 Mo.
set -euo pipefail
DEST="${1:-$HOME/sc_tmp}"
IDS="0001 0002 0003 0004 0005 0006 0007 0008 0009 \
     0152 0153 0154 0155 0156 0157 0158 0159 0160 \
     0252 0253 0254 0255 0256 0257 0258 0259 0260"

rm -rf "$DEST"
git clone --filter=blob:none --no-checkout --depth 1 \
    https://github.com/PMDCollab/SpriteCollab.git "$DEST"
cd "$DEST"
git sparse-checkout init --cone
git sparse-checkout set $(for i in $IDS; do printf 'sprite/%s ' "$i"; done)
git checkout
echo "SpriteCollab prêt dans $DEST ($(du -sh . | cut -f1))"
