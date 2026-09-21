#!/bin/bash

# Obtener ruta absoluta
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ICON_DIR="${PROJECT_ROOT}/assets"
ICON_PATH="${ICON_DIR}/talos-icon.png"

if [ ! -f "$ICON_PATH" ]; then
    echo "🎨 Creando ícono placeholder para TALOS..."
    mkdir -p "$ICON_DIR"

    # Verificar si ImageMagick está instalado
    if command -v convert &> /dev/null; then
        convert -size 256x256 xc:'#111113' \
            -fill '#f59e0b' -draw "circle 128,128 128,40" \
            -fill '#0b0b0d' -draw "circle 128,128 128,50" \
            -fill '#f59e0b' -draw "polygon 128,60 185,160 71,160" \
            -fill white -pointsize 64 -gravity center -annotate +0+5 "T" \
            "$ICON_PATH"
        echo "✅ Ícono creado: $ICON_PATH"
    else
        echo "⚠️  ImageMagick no está instalado"
        echo "   Instalalo con: sudo apt install imagemagick"
        echo "   O descargá un ícono manualmente y guardalo en: $ICON_PATH"
        exit 1
    fi
else
    echo "✓ Ícono ya existe: $ICON_PATH"
fi
