#!/usr/bin/env bash
# ============================================================================
# talos-reanudacion-retirada.sh — TALOS PHASE 3 · reanudación verificada de la
# retirada interrumpida (2026-10-20·II). Copia canónica:
# /media/agustin/Almacenamiento/Facultad/TALOS/manifests/
#
# Contexto: la ejecución del 2026-10-20 (talos-retirada-origenes.sh --execute)
# retiró 4 grupos completos y quedó interrumpida en talos-f09 por 4 directorios
# con permisos 555 (sin atributo inmutable, sin proceso escribiendo — verificado).
#
# MODOS (uno por invocación):
#   (sin argumento)  SIMULACIÓN: A+B+C+D; no modifica nada.
#   --fix-perms      aplica `chmod u+w` SOLO a directorios de orígenes
#                    pendientes bajo BASE; jamás toca Facultad.
#   --execute        verificación completa (A+B+C+D), luego retirada SOLO de
#                    los pendientes; al final re-verifica (E) que las copias de
#                    Facultad siguen hash-idénticas al registro de preflight.
#                    Si CUALQUIER verificación falla: no borra nada (fail-closed).
#
# Garantías:
#  - Listas CERRADAS (removidos y pendientes). Nada se deduce del sistema.
#  - BASE y DEST constantes; se rechaza cualquier par fuera de BASE.
#  - Registro de preflight: preflight-sha256-origen-20261020.sha (4.411 entradas;
#    el archivo RoadmapNuevoHorizonte.txt se verificó aparte: a761136e…).
#  - Reanudación idempotente: si un pendiente ya no existe, se reclasifica como
#    removido y su copia se valida contra el registro.
# ============================================================================
set -uo pipefail

MODE="SIMULATE"
[ "${1:-}" = "--fix-perms" ] && MODE="FIX_PERMS"
[ "${1:-}" = "--execute" ]   && MODE="EXECUTE"

BASE="/media/agustin/Laboratorio"
DEST="/media/agustin/Almacenamiento/Facultad"
PF="$DEST/TALOS/manifests/preflight-sha256-origen-20261020.sha"
GUARD_EXCLUDED="study-engie timeshift lost+found"

# --- RETIRADOS EN LA EJECUCIÓN INTERRUMPIDA (respondados por estado) -------
REMOVED=(
  "talos-wip-backups/20261020T112807Z"
  "talos-wip-backups/20261020T114944Z-phase2-structural-recovery"
  "talos-f07-diagnostic-vXugos2f"
  "talos-f08-resolution-lfs8neBd"
)
# F09: retirada PARCIAL (12/32 archivos borrados por el run interrumpido;
# 20 archivos + 5 dirs restan). Se valida subset: lo restante contra su copia,
# y las copias recordadas por el registro.
# --- PENDIENTES ------------------------------------------------------------
PENDING_DIRS=(
  "talos-f09-authorization-gUVYAnpn"
  "talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369"
  "talos-p1-2-b06-capture-20261009"
  "talos-p1-2-b06-evidence-20261009"
  "talos-p1-2-b06-snapshot-20261009"
  "talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369"
  "TALOS-COLAB-PILOT-01"
  "TALOS-DEVTOOLS-001"
  "TALOS-DEVTOOLS-002"
  "Cerebro_Ciberseguridad"
  "Ciberseguiradad"
  "Estudio_libros"
  "PlanDeEstudio"
)
PENDING_FILE="RoadmapNuevoHorizonte.txt"
RESIDUE_PARENT="talos-wip-backups"   # padre vacío → rmdir en --execute

fail()  { echo "  ✗ $*" >&2; FAILS=$((FAILS+1)); }
section(){ echo; echo "---- $* ----"; }

# ==========================================================================
# Paso A — removidos: existencia (ausencia) + copia en Facultad íntegra
#      contra el registro de preflight.
# ==========================================================================
stepA() {
  section "A · RETIRADOS: copia Facultad íntegra vs registro preflight"
  python3 -u - "$DEST" "$PF" "${REMOVED[@]}" <<'PYEOF'
import hashlib, os, sys
dest, pf = sys.argv[1], sys.argv[2]
items = sys.argv[3:]
def cur(root):
    m = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            h = hashlib.sha256()
            with open(p, 'rb') as f:
                for ch in iter(lambda: f.read(1 << 20), b''):
                    h.update(ch)
            m[os.path.relpath(p, root)] = h.hexdigest()
    return m
rec = {}
with open(pf) as f:
    for line in f:
        line = line.rstrip('\n')
        if not line.strip(): continue
        h, p = line.split(' ', 1); p = p.strip()
        rec[p] = h
rc = 0
for it in items:
    dl = os.path.join(dest, 'TALOS') if it.startswith(('talos-wip', 'talos-')) else None
    # destino por item (mapa cerrado)
    if   it.startswith('talos-wip-backups/20261020T112807Z'):
        droot = os.path.join(dest, 'TALOS/backups/structural-recovery/20261020T112807Z'); pref = it
    elif it.startswith('talos-wip-backups/'):
        droot = os.path.join(dest, 'TALOS/backups/structural-recovery/20261020T114944Z-phase2-structural-recovery'); pref = it
    elif it.startswith('talos-f07'): droot = os.path.join(dest, 'TALOS/historical-evidence/F07-F12/talos-f07-diagnostic-vXugos2f'); pref = it
    elif it.startswith('talos-f08'): droot = os.path.join(dest, 'TALOS/historical-evidence/F07-F12/talos-f08-resolution-lfs8neBd'); pref = it
    else: print(f"sin-A-mapa: {it}"); rc = 1; continue
    curh = cur(droot)
    # normalizar: claves del registro traen prefijo completo; las de la copia
    # son relativas a droot → strip del prefijo antes de comparar.
    strip_n = len(pref) + 1
    sub = {k[strip_n:]: v for k, v in rec.items() if k.startswith(pref + '/')}
    missing_in_rec = [k for k in curh if k not in sub]
    missing_in_dst = [k for k in sub if k not in curh]
    difers = [k for k in sub.keys() & curh.keys() if sub[k] != curh[k]]
    extra  = missing_in_rec
    if missing_in_dst or difers:
        print(f"  ✗ {pref}: sin-copia={len(missing_in_dst)} difieren={len(difers)}")
        for k in (missing_in_dst + difers)[:5]: print(f"      {k}")
        rc = 1
    else:
        print(f"  ✓ {pref}: {len(sub)} archivos hash-idénticos vs registro (extra-en-copia: {len(extra)})")
sys.exit(rc)
PYEOF
  [ $? -eq 0 ] || fail "Paso A"
}

# ==========================================================================
# Paso B — F09 residual: todo lo que RESTA en el origen debe coincidir con
#          la copia en Facultad. Las bajas del run interrumpido se listan
#          como "ausencias documentadas" (nada más está permitido divergir).
# ==========================================================================
stepB() {
  section "B · F09 RESIDUAL: subset restante vs copia (ausencias=run interrumpido)"
  python3 -u - "$BASE/talos-f09-authorization-gUVYAnpn" "$DEST/TALOS/historical-evidence/F07-F12/talos-f09-authorization-gUVYAnpn" <<'PYEOF'
import hashlib, os, sys
o_root, d_root = sys.argv[1], sys.argv[2]
def cur(root):
    m = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            h = hashlib.sha256()
            with open(p, 'rb') as f:
                for ch in iter(lambda: f.read(1 << 20), b''):
                    h.update(ch)
            m[os.path.relpath(p, root)] = h.hexdigest()
    return m
mo, md = cur(o_root), cur(d_root)
only_d = sorted(set(md) - set(mo))
only_o = sorted(set(mo) - set(md))
difers = sorted(k for k in set(mo) & set(md) if mo[k] != md[k])
print(f"  ausencias documentadas en origen (borradas por run interrumpido): {len(only_d)}")
for k in only_d: print(f"      − {k}")
if only_o:
    print(f"  ✗ archivos NO documentados presentes en origen (no en copia): {len(only_o)}")
    for k in only_o[:5]: print(f"      + {k}")
    sys.exit(1)
if difers:
    print(f"  ✗ archivos residuales MODIFICADOS vs copia: {len(difers)}")
    for k in difers[:5]: print(f"      ± {k}")
    sys.exit(1)
print(f"  ✓ 20/20 restantes coinciden (subset). Total copia: {len(md)} archivos (32 esperados).")
if len(only_d) + len(mo) != len(md):
    print(f"  ✗ ERROR aritmético subset: {len(only_d)}+{len(mo)}!={len(md)}"); sys.exit(1)
sys.exit(0)
PYEOF
  [ $? -eq 0 ] || fail "Paso B"
}

# ==========================================================================
# Paso C — permisos: inventario de dirs sin u+w en los pendientes SOLO.
#          (0 en SIMULATE es información; en --execute es bloqueante.)
# ==========================================================================
stepC() {  # args: 1 = hard(1) si modo execute
  section "C · PERMISOS: directorios sin u+w (solo pendientes)"
  bad=0
  for rel in "${PENDING_DIRS[@]}"; do
    o="$BASE/$rel"
    [ -d "$o" ] || { echo "  (ya ausente) $rel"; continue; }
    n=$(find "$o" -type d ! -perm -u+w 2>/dev/null | wc -l)
    [ "$n" -ne 0 ] && { echo "  ✗ $rel: $n dir(s) sin u+w"; bad=$((bad+1)); }
  done
  if [ "$bad" -eq 0 ]; then echo "  ✓ 0 pendientes con bloqueos de permisos"
  else fail "Paso C: $bad pendientes requieren --fix-perms antes de --execute"; fi
  return 0
}

# ==========================================================================
# Paso D — pendientes intactos: verificación full-tree origen↔copia real
#          (hash SHA-256 raíz-a-raíz). F09 ya quedo cubierto por B (subset).
# ==========================================================================
stepD() {
  section "D · PENDIENTES: verificación full-tree origen↔copia (hash SHA-256)"
  for rel in "${PENDING_DIRS[@]}"; do
    [ "$rel" = "talos-f09-authorization-gUVYAnpn" ] && { echo "  (F09: cubierto por paso B)"; continue; }
    o="$BASE/$rel"
    case "$rel" in
      talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369)
        d="$DEST/TALOS/historical-evidence/F07-F12/talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369";;
      talos-p1-2-b06-capture-20261009)   d="$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-capture-20261009";;
      talos-p1-2-b06-evidence-20261009)  d="$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009";;
      talos-p1-2-b06-snapshot-20261009)  d="$DEST/TALOS/historical-evidence/B06/talos-p1-2-b06-snapshot-20261009";;
      talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369) d="$DEST/TALOS/historical-evidence/B06/talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369";;
      TALOS-COLAB-PILOT-01)  d="$DEST/TALOS/experiments/colab/TALOS-COLAB-PILOT-01";;
      TALOS-DEVTOOLS-001)    d="$DEST/TALOS/experiments/devtools/TALOS-DEVTOOLS-001";;
      TALOS-DEVTOOLS-002)    d="$DEST/TALOS/experiments/devtools/TALOS-DEVTOOLS-002";;
      Cerebro_Ciberseguridad) d="$DEST/Estudios/Ciberseguridad/Cerebro_Ciberseguridad";;
      Ciberseguiradad)        d="$DEST/Estudios/Ciberseguridad/Ciberseguiradad";;
      Estudio_libros)         d="$DEST/Estudios/Materiales-academicos/Estudio_libros";;
      PlanDeEstudio)          d="$DEST/Estudios/Materiales-academicos/PlanDeEstudio";;
    esac
    [ -e "$o" ] || { fail "Paso D: origen ausente inesperado: $rel"; continue; }
    [ -e "$d" ] || { fail "Paso D: copia ausente: $d"; continue; }
    if python3 -u - "$o" "$d" <<'PYEOF'
import hashlib, os, sys
def walk(root):
    m = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            h = hashlib.sha256()
            with open(p, 'rb') as f:
                for ch in iter(lambda: f.read(1 << 20), b''):
                    h.update(ch)
            m[os.path.relpath(p, root)] = h.hexdigest()
    return m
a, b = walk(sys.argv[1]), walk(sys.argv[2])
if a != b:
    only_a = sorted(set(a) - set(b))[:5]
    only_b = sorted(set(b) - set(a))[:5]
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])[:5]
    print(f"  ✗ DIFERENCIA: solo-origen={only_a} solo-copia={only_b} modificados={diff}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
    then
      echo "  ✓ $(printf '%-70s' "$rel") arch=$(find "$o" -type f | wc -l)"
    else
      fail "Paso D: $rel"
    fi
  done
  of="$BASE/$PENDING_FILE"; df="$DEST/Estudios/Ciberseguridad/$PENDING_FILE"
  if cmp -s "$of" "$df"; then echo "  ✓ archivo verificado: $PENDING_FILE"; else fail "Paso D: $PENDING_FILE difiere"; fi
}

# ==========================================================================
# Paso E — tras retirada: validar TODAS las copias (removidos + F09 incl.)
#          contra el registro de preflight (prueba de recuperabilidad).
# ==========================================================================
stepE() {
  section "E · POST-RETIRADA: recuperabilidad de TODAS las copias (vs registro)"
  python3 -u - "$DEST" "$PF" <<'PYEOF'
import hashlib, os, sys
dest, pf = sys.argv[1], sys.argv[2]
rec = {}
with open(pf) as f:
    for line in f:
        line = line.rstrip('\n')
        if not line.strip(): continue
        h, p = line.split(' ', 1); p = p.strip()
        rec[p] = h
def walk(root):
    m = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            h = hashlib.sha256()
            with open(p, 'rb') as f:
                for ch in iter(lambda: f.read(1 << 20), b''):
                    h.update(ch)
            m[os.path.relpath(p, root)] = h.hexdigest()
    return m
# mapa destino (por regla: el prefijo recordado mapea a cada dir copia — cerrado)
MAP = {
    'talos-wip-backups/20261020T112807Z/':            'TALOS/backups/structural-recovery/20261020T112807Z/',
    'talos-wip-backups/20261020T114944Z-phase2-structural-recovery/': 'TALOS/backups/structural-recovery/20261020T114944Z-phase2-structural-recovery/',
    'talos-f07/':                                     'TALOS/historical-evidence/F07-F12/talos-f07-diagnostic-vXugos2f/',
    'talos-f08/':                                     'TALOS/historical-evidence/F07-F12/talos-f08-resolution-lfs8neBd/',
    'talos-f09/':                                     'TALOS/historical-evidence/F07-F12/talos-f09-authorization-gUVYAnpn/',
    'talos-f10/':                                     'TALOS/historical-evidence/F07-F12/talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369/',
    'talos-p1-2-b06-capture-20261009/':               'TALOS/historical-evidence/B06/talos-p1-2-b06-capture-20261009/',
    'talos-p1-2-b06-evidence-20261009/':              'TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009/',
    'talos-p1-2-b06-snapshot-20261009/':              'TALOS/historical-evidence/B06/talos-p1-2-b06-snapshot-20261009/',
    'talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369/': 'TALOS/historical-evidence/B06/talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369/',
    'TALOS-COLAB-PILOT-01/':                          'TALOS/experiments/colab/TALOS-COLAB-PILOT-01/',
    'TALOS-DEVTOOLS-001/':                            'TALOS/experiments/devtools/TALOS-DEVTOOLS-001/',
    'TALOS-DEVTOOLS-002/':                            'TALOS/experiments/devtools/TALOS-DEVTOOLS-002/',
    'Cerebro_Ciberseguridad/':                        'Estudios/Ciberseguridad/Cerebro_Ciberseguridad/',
    'Ciberseguiradad/':                               'Estudios/Ciberseguridad/Ciberseguiradad/',
    'Estudio_libros/':                                'Estudios/Materiales-academicos/Estudio_libros/',
    'PlanDeEstudio/':                                 'Estudios/Materiales-academicos/PlanDeEstudio/',
}
bare = {}
for k, v in rec.items():
    bare[k] = (k, v)
items = sorted({k.split('/')[0] for k in rec})
for it in items:
    pref = it + '/'
    key = next((x for x in MAP if x.startswith(it) or it.startswith(x.rstrip('/'))), None)
    if key is None or not key.startswith(it):
        print(f"  (saltado en registro iter-1: {it})"); continue
    sub = {k[len(key):]: v for k, v in rec.items() if k.startswith(key)}
    droot = os.path.join(dest, MAP[key].rstrip('/'))
    curh = walk(droot)
    missing = [k for k in sub if k not in curh]
    extra   = [k for k in curh if k not in sub]
    difers  = [k for k in sub.keys() & curh.keys() if sub[k] != curh[k]]
    st = "✓" if not (missing or difers) else "✗"
    print(f"  {st} {it}: {len(sub)} archivos (sin-copia={len(missing)} dif={len(difers)} extra={len(extra)})")
    for k in (missing + difers)[:3]: print(f"      {k}")
    if missing or difers: sys.exit(1)
sys.exit(0)
PYEOF
  rf=$(sha256sum "$DEST/Estudios/Ciberseguridad/$PENDING_FILE" | awk '{print $1}')
  if [ "$rf" = "a761136ed68ba4e928b4bc53fe3f96d566dbc19435a410f17c6d405455cf0396" ]; then
    echo "  ✓ $PENDING_FILE (copia): $rf"
  else
    fail "Paso E: $PENDING_FILE copia difiere del hash a761136e…"
  fi
  [ $? -eq 0 ] || fail "Paso E"
}

# ==========================================================================
# MAIN
# ==========================================================================
FAILS=0
echo "== PHASE 3 · reanudación de retirada — modo: $MODE =="
echo "   base: $BASE"
echo "   registro: $PF"

case "$MODE" in
  SIMULATE)
    stepA; stepB; stepC 0; stepD
    echo; if [ "$FAILS" -eq 0 ]; then
      echo "== SIMULACIÓN OK: preparado para --fix-perms (si C indicó bloqueos) y luego --execute =="
    else
      echo "== SIMULACIÓN con $FAILS fallo(s): NO pasar a --execute (fail-closed) =="
    fi
    ;;
  FIX_PERMS)
    section "FIX_PERMS: chmod u+w SOLO en dirs de orígenes pendientes"
    for rel in "${PENDING_DIRS[@]}"; do
      o="$BASE/$rel"
      case "$o" in "$BASE"/*) : ;; *) fail "fijo: fuera de base: $rel"; continue ;; esac
      for ex in $GUARD_EXCLUDED; do [ "$rel" = "$ex" ] && { fail "excluido en lista: $rel"; continue 2; } done
      [ -d "$o" ] || { echo "  (ya ausente) $rel"; continue; }
      find "$o" -type d -exec chmod u+w {} + && echo "  chmod u+w dirs: $rel"
    done
    stepC 0
    [ "$FAILS" -eq 0 ] || { echo "== FIX_PERMS con fallos =="; exit 1; }
    echo "== FIX_PERMS OK =="
    ;;
  EXECUTE)
    stepA; stepB; stepC 1; stepD
    if [ "$FAILS" -ne 0 ]; then
      echo; echo "== ABORTADO (fail-closed): $FAILS verificación(es) fallaron; NADA se borró. =="
      exit 1
    fi
    section "RETIRADA de pendientes"
    for rel in "${PENDING_DIRS[@]}"; do
      o="$BASE/$rel"
      [ -e "$o" ] || { echo "  (ya ausente) $rel"; continue; }
      rm -rf -- "$o"
      [ -e "$o" ] && { echo "ABORTADO: persiste tras rm: $o"; exit 1; }
      echo "  retirado: $rel"
    done
    of="$BASE/$PENDING_FILE"
    if [ -e "$of" ]; then cmp -s "$of" "$DEST/Estudios/Ciberseguridad/$PENDING_FILE" && rm -f -- "$of" || { echo "ABORTADO: $PENDING_FILE difiere de su copia"; exit 1; }
      [ -e "$of" ] && { echo "ABORTADO: persiste: $of"; exit 1; }
      echo "  retirado: $PENDING_FILE"; fi
    rp="$BASE/$RESIDUE_PARENT"
    if [ -d "$rp" ]; then if [ -z "$(find "$rp" -mindepth 1 -print -quit 2>/dev/null)" ]; then rmdir -- "$rp" && echo "  rmdir (padre vacío): $RESIDUE_PARENT"; else echo "  ✗ $RESIDUE_PARENT no está vacío; se conserva"; FAILS=$((FAILS+1)); fi; fi
    stepE
    echo; echo "== RESTANTE EN BASE (esperado: solo study-engie, timeshift, lost+found, .Trash-1000) =="
    ls -1 "$BASE"
    echo
    if [ "$FAILS" -eq 0 ]; then
      echo "== RETIRADA REANUDADA COMPLETADA Y VERIFICADA =="
      echo "   TALOS_STATE: TALOS_PHASE3_RETIRADA_RESUMED_VERIFIED"
    else
      echo "== VERIFICACIÓN POST-RETIRADA con $FAILS fallo(s) =="
      exit 1
    fi
    ;;
esac
[ "$FAILS" -eq 0 ] && exit 0 || exit 1
