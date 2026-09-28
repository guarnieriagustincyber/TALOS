#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/../../.." && pwd)"
DB_PATH="$ROOT/data/student/student_state.db"
BACKUP_PATH="${1:-}"

if [[ -z "$BACKUP_PATH" ]]; then
  printf 'Uso: bash %s <ruta-al-backup.db>\n' "$0" >&2
  exit 2
fi

if [[ "$BACKUP_PATH" != /* ]]; then
  BACKUP_PATH="$ROOT/$BACKUP_PATH"
fi

case "$BACKUP_PATH" in
  "$ROOT"/benchmark/backups/*) ;;
  *)
    printf 'El backup debe estar dentro de benchmark/backups/: %s\n' "$BACKUP_PATH" >&2
    exit 2
    ;;
esac

if [[ ! -f "$BACKUP_PATH" ]]; then
  printf 'Backup no encontrado: %s\n' "$BACKUP_PATH" >&2
  exit 1
fi

if "$ROOT/.venv/bin/python" -c 'import socket; s=socket.socket(); s.settimeout(0.5); s.connect(("127.0.0.1", 8000)); s.close()' 2>/dev/null; then
  printf 'El backend responde en 127.0.0.1:8000. Detenelo antes de restaurar la DB.\n' >&2
  exit 1
fi

TEMP_PATH="$(mktemp "$ROOT/data/student/.student_state.restore.XXXXXX")"
trap 'rm -f -- "$TEMP_PATH"' EXIT
cp -- "$BACKUP_PATH" "$TEMP_PATH"
mv -f -- "$TEMP_PATH" "$DB_PATH"
trap - EXIT

printf 'Estado restaurado desde: %s\n' "$BACKUP_PATH"
