#!/usr/bin/env bash
# ============================================================================
# talos-retirada-origenes.sh — TALOS PHASE 3 · retirada verificada de orígenes
# (2026-10-20). Copia canónica: Facultad/TALOS/manifests/
#
# Uso:
#   bash talos-retirada-origenes.sh              # SIMULACIÓN (no borra nada)
#   bash talos-retirada-origenes.sh --execute    # ejecución real
#
# Garantías:
#  - Lista CERRADA de 18 pares origen↔destino (nada se deduce del sistema).
#  - Dos pasadas: (1) TODAS las verificaciones; si cualquier par falla, NO
#    se borra nada (fail-closed, sin borrados parciales silenciosos).
#  - Por par: existencia en ambos lados + conteo de archivos + bytes totales
#    + re-hash SHA-256 full-tree (origen vs copia, raíz-a-raíz).
#  - Rechaza cualquier ruta fuera de BASE o incluida en la lista de exclusión.
# ============================================================================
set -uo pipefail

MODE="SIMULATE"
[ "${1:-}" = "--execute" ] && MODE="EXECUTE"

BASE="/media/agustin/Laboratorio"
DEST="/media/agustin/Almacenamiento/Facultad"
EXCLUDED_KNOWN="study-engie timeshift lost+found"

PAIRS=(
  "talos-wip-backups/20261020T112807Z|$DEST/TALOS/backups/structural-recovery/20261020T112807Z"
  "talos-wip-backups/20261020T114944Z-phase2-structural-recovery|$DEST/TALOS/backups/structural-recovery/20261020T114944Z-phase2-structural-recovery"
  "talos-f07-diagnostic-vXugos2f|$DEST/TALOS/historical-evidence/F07-F12/talos-f07-diagnostic-vXugos2f"
  "talos-f08-resolution-lfs8neBd|$DEST/TALOS/historical-evidence/F07-F12/talos-f08-resolution-lfs8neBd"
  "talos-f09-authorization-gUVYAnpn|$DEST/TALOS/historical-evidence/F07-F12/talos-f09-authorization-gUVYAnpn"
  "talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369|$DEST/TALOS/historical-evidence/F07-F12/talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369"
  "talos-p1-2-b06-capture-20261009|$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-capture-20261009"
  "talos-p1-2-b06-evidence-20261009|$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009"
  "talos-p1-2-b06-snapshot-20261009|$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-snapshot-20261009"
  "talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369|$DEST/TALOS/historical-evidence/B06/talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369"
  "TALOS-COLAB-PILOT-01|$DEST/TALOS/experiments/colab/TALOS-COLAB-PILOT-01"
  "TALOS-DEVTOOLS-001|$DEST/TALOS/experiments/devtools/TALOS-DEVTOOLS-001"
  "TALOS-DEVTOOLS-002|$DEST/TALOS/experiments/devtools/TALOS-DEVTOOLS-002"
  "Cerebro_Ciberseguridad|$DEST/Estudios/Ciberseguridad/Cerebro_Ciberseguridad"
  "Ciberseguiradad|$DEST/Estudios/Ciberseguridad/Ciberseguiradad"
  "Estudio_libros|$DEST/Estudios/Materiales-academicos/Estudio_libros"
  "PlanDeEstudio|$DEST/Estudios/Materiales-academicos/PlanDeEstudio"
  "RoadmapNuevoHorizonte.txt|$DEST/Estudios/Ciberseguridad/RoadmapNuevoHorizonte.txt"
)

verify_pair() {
  local rel="$1" dst="$2" o="$BASE/$rel"
  case "$o" in "$BASE"/*) : ;; *) echo "FATAL: par fuera de base: $rel"; return 1 ;; esac
  for ex in $EXCLUDED_KNOWN; do
    [ "$rel" = "$ex" ] && { echo "FATAL: item excluido en lista: $rel"; return 1; }
  done
  [ -e "$o" ]  || { echo "  ✗ origen ausente:        $o";  return 1; }
  [ -e "$dst" ] || { echo "  ✗ copia ausente:         $dst"; return 1; }
  if [ -f "$o" ]; then
    cmp -s "$o" "$dst" && { echo "  ✓ archivo verificado: $rel"; return 0; }
    echo "  ✗ archivo difiere: $rel"; return 1
  fi
  # re-hash full-tree del par (Python: robusto ante espacios y prefijos)
  if python3 - "$o" "$dst" <<'PYEOF'
import hashlib, os, sys
def walk(root):
    m = {}
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            h = hashlib.sha256()
            with open(p, 'rb') as f:
                for ch in iter(lambda: f.read(1 << 20), b''):
                    h.update(ch)
            m[os.path.relpath(p, root)] = h.hexdigest()
    return m
a, b = sys.argv[1], sys.argv[2]
ma, mb = walk(a), walk(b)
if ma != mb:
    only_a = sorted(set(ma) - set(mb))[:5]
    only_b = sorted(set(mb) - set(ma))[:5]
    diff = sorted(k for k in set(ma) & set(mb) if ma[k] != mb[k])[:5]
    print(f"  ✗ HASHES difieren: solo-origen={only_a} solo-destino={only_b} modificados={diff}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
  then
    echo "  ✓ $(printf '%-76s' "$rel") arch=$(find "$o" -type f | wc -l) bytes=$(du -sb "$o" | cut -f1)"
    return 0
  fi
  return 1
}

echo "== PHASE 3 retirada de orígenes — modo: $MODE =="
echo "   base: $BASE"
echo "   destinos verificados en: $DEST"
PASS_OK=0; PASS_FAIL=0
FAIL_ITEMS=()
for pair in "${PAIRS[@]}"; do
  rel="${pair%%|*}"; dst="${pair#*|}"
  if verify_pair "$rel" "$dst"; then
    PASS_OK=$((PASS_OK+1))
  else
    PASS_FAIL=$((PASS_FAIL+1)); FAIL_ITEMS+=("$rel")
  fi
done
echo "== pasada 1 finalizada: OK=$PASS_OK / FAIL=$PASS_FAIL (esperado: 18/18) =="
if [ "$PASS_FAIL" -ne 0 ]; then
  echo "ABORTADO (fail-closed): NO se borró nada."
  printf '  FALLÓ: %s\n' "${FAIL_ITEMS[@]}"
  exit 1
fi
if [ "$MODE" = "SIMULATE" ]; then
  echo "== SIMULACIÓN OK: 18/18 pares verificados; --execute retiraría los 17 orígenes =="
  exit 0
fi
echo "== pasada 2: ejecutando retirada =="
removed=0
for pair in "${PAIRS[@]}"; do
  rel="${pair%%|*}"; o="$BASE/$rel"
  if [ ! -e "$o" ]; then echo "ABORTADO: precondición perdida: $o"; exit 1; fi
  if [ -f "$o" ]; then rm -f -- "$o"; else rm -rf -- "$o"; fi
  [ -e "$o" ] && { echo "ABORTADO: persiste tras rm: $o"; exit 1; }
  echo "  retirado: $rel"
  removed=$((removed+1))
done
echo "== retirada completa: $removed pares =="
echo "== estado final de $BASE/: =="
ls -1 "$BASE"
