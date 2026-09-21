#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOCAL_KNOWLEDGE="data/web_state/knowledge_store.db"
REMOTE_FOLDER="gdrive:talos_reindex"

if [ ! -f "$LOCAL_KNOWLEDGE" ]; then
    echo "❌ Error: No se encontró $LOCAL_KNOWLEDGE"
    exit 1
fi

echo "🚀 [1/1] Subiendo knowledge_store.db a Google Drive ($REMOTE_FOLDER)..."
rclone copy "$LOCAL_KNOWLEDGE" "$REMOTE_FOLDER" -P

echo ""
echo "✅ knowledge_store.db subido con éxito."
echo "👉 Ahora podés ejecutar o reanudar el notebook en Google Colab para indexar."
