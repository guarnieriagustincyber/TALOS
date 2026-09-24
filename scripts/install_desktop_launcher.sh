#!/bin/bash

# Obtener la ruta absoluta del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Instalando lanzador de escritorio para TALOS..."

# Asegurar que el ícono existe
"${SCRIPT_DIR}/create_placeholder_icon.sh"

# Crear archivo .desktop con rutas absolutas
cat > /tmp/talos.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=TALOS - Sistema de Estudio
Comment=Sistema de Estudio Epistémico con IA
Exec=/bin/bash -c 'cd ${PROJECT_ROOT} && (${PROJECT_ROOT}/.venv/bin/python3 start_talos.py || python3 start_talos.py)'
Icon=${PROJECT_ROOT}/assets/talos-icon.png
Terminal=false
Categories=Education;Development;
Keywords=study;learning;ai;education;
StartupNotify=false
EOF

# Copiar al directorio de aplicaciones del usuario
mkdir -p ~/.local/share/applications
cp /tmp/talos.desktop ~/.local/share/applications/talos.desktop

# Actualizar base de datos de aplicaciones
update-desktop-database ~/.local/share/applications 2>/dev/null || true

# Copiar también al escritorio si existe
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || true)
if [ -z "$DESKTOP_DIR" ] || [ ! -d "$DESKTOP_DIR" ]; then
    if [ -d "$HOME/Escritorio" ]; then
        DESKTOP_DIR="$HOME/Escritorio"
    elif [ -d "$HOME/Desktop" ]; then
        DESKTOP_DIR="$HOME/Desktop"
    fi
fi

if [ -n "$DESKTOP_DIR" ] && [ -d "$DESKTOP_DIR" ]; then
    cp /tmp/talos.desktop "$DESKTOP_DIR/talos.desktop"
    chmod +x "$DESKTOP_DIR/talos.desktop"
    echo "✓ Ícono creado en el escritorio: $DESKTOP_DIR/talos.desktop"
fi

# Hacer ejecutable el archivo de aplicaciones
chmod +x ~/.local/share/applications/talos.desktop

echo "✅ Lanzador instalado exitosamente!"
echo ""
echo "📍 Ubicaciones:"
echo "  - Menú de aplicaciones: ~/.local/share/applications/talos.desktop"
if [ -n "$DESKTOP_DIR" ] && [ -d "$DESKTOP_DIR" ]; then
    echo "  - Escritorio: $DESKTOP_DIR/talos.desktop"
fi
echo ""
echo "💡 Para usar:"
echo "  - Buscá 'TALOS' en el menú de aplicaciones"
echo "  - O hacé doble clic en el ícono del escritorio"
echo ""
echo "🗑️  Para desinstalar:"
echo "  rm -f ~/.local/share/applications/talos.desktop"
if [ -n "$DESKTOP_DIR" ]; then
    echo "  rm -f \"$DESKTOP_DIR/talos.desktop\""
fi

# Limpiar
rm -f /tmp/talos.desktop
