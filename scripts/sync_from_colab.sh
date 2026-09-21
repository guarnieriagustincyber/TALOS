#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOCAL_TARGET_DIR="data/web_state"
LOCAL_VECTOR_DB="$LOCAL_TARGET_DIR/vector_store.db"
REMOTE_VECTOR_DB="gdrive:talos_reindex/vector_store.db"

echo "📥 [1/2] Descargando vector_store.db desde Google Drive..."
rclone copy "$REMOTE_VECTOR_DB" "$LOCAL_TARGET_DIR" -P

if [ -f "$LOCAL_VECTOR_DB" ]; then
    echo ""
    echo "🔍 [2/2] Verificando integridad de la base vectorial..."
    python3 -c "
import sqlite3
con = sqlite3.connect('$LOCAL_VECTOR_DB')
try:
    total = con.execute('SELECT COUNT(*) FROM chunk_embeddings').fetchone()[0]
    print(f'✅ Verificación exitosa: {total:,} vectores disponibles en $LOCAL_VECTOR_DB')
except Exception as e:
    print(f'⚠️ Error al leer chunk_embeddings: {e}')
finally:
    con.close()
"
    echo "🎉 ¡Sincronización completada! TALOS ya tiene los nuevos vectores."
else
    echo "❌ Error: No se pudo descargar vector_store.db"
    exit 1
fi
