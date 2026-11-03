# Checkpoint 072 — investigación externa de baseline authority

Fecha: 2026-10-01

## A. Resultado ejecutivo

```text
RESULT = NOT_RESOLVED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
F058_STATUS = NOT_RECOVERED
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
EXTERNAL_SEARCH_EXECUTED = YES (búsqueda pública, sólo lectura)
```

La investigación externa acotada no encontró una fuente primaria pública y
verificable que establezca una autoridad normativa para el baseline/snapshot
requerido por A-PRE-0. No se recuperó `f058…`, no apareció una designación
normativa equivalente y no pudo reconstruirse una cadena de autoridad.

`NOT_FOUND` significa que las búsquedas públicas descritas aquí no devolvieron
la evidencia solicitada. **No** significa `PROVEN_ABSENT`: las respuestas
404, la falta de resultados y la inaccesibilidad pública no demuestran que el
artefacto, el repositorio o una designación no existan en fuentes privadas,
renombradas, retiradas o no indexadas.

La investigación se efectuó en respuesta a la autorización vigente de CP071.
No se hizo búsqueda autenticada, contacto con terceros, clonación ni
ejecución de código. No se realizó ninguna resolución normativa.

## B. Estado de entrada y objetivo de identidad

CP071 autoriza la búsqueda, pero no resuelve la autoridad:

```text
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
REOPEN_PATH_A = YES
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
```

El ledger local cita como `current_normative_spec`:

```text
path = /home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md
sha256 = f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4
present_in_qualified_overlay = false
```

El mismo ledger identifica el overlay cualificado declarado como:

```text
path = /home/agustin/apre-runner/cpython-3.10.21/evidence/a-pre-snapshot-identity-20261001/overlay-async-seccomp-v4
commit = 2b2083795602f9099db43bb7ee35b0c030bdf51b
tree = d7ae2718c0a969fd1cf8eee0678f0d6f209c59a7
```

Estos son datos de partida registrados localmente, no evidencia externa que
acredite la autoridad de la referencia. El hash completo se buscó tal como
aparece en el ledger; no se generaron variantes arbitrarias.

## C. Matriz de evidencia externa

Consultas y endpoints fueron comprobados el 2026-10-01. “Sin evidencia” en
una columna indica que la fuente no permitió verificar ese elemento.

| EVIDENCE | SOURCE | IDENTITY | AUTHORITY | SCOPE | PRECEDENCE | SNAPSHOT_RELATION | STRENGTH | LIMITATIONS |
|---|---|---|---|---|---|---|---|---|
| Disponibilidad del repositorio oficial solicitado | [GitHub repository API](https://api.github.com/repos/guarnieriagustincyber/TALOS), [página del repositorio](https://github.com/guarnieriagustincyber/TALOS), [árbol main](https://github.com/guarnieriagustincyber/TALOS/tree/main), [releases](https://github.com/guarnieriagustincyber/TALOS/releases) | No verificable desde esas URLs | Sin evidencia | Sin evidencia | Sin evidencia | Sin evidencia | Primaria en caso de disponibilidad; las solicitudes devolvieron 404 | Un 404 anónimo no distingue entre repositorio privado, inexistente, movido, retirado o inaccesible. No prueba ausencia. |
| Búsqueda de repositorio público TALOS bajo la cuenta | [GitHub repository search](https://api.github.com/search/repositories?q=TALOS+user%3Aguarnieriagustincyber) | Sin resultado (`total_count=0`) | Sin evidencia | Sin evidencia | Sin evidencia | Sin evidencia | Índice público; resultado verificable de búsqueda | No encuentra un repositorio público con esa consulta; no descarta nombres distintos, mirrors no indexados ni repositorios privados. |
| Identificador exacto `f058…` en commits públicos | [GitHub commit search](https://api.github.com/search/commits?q=f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4) | Sin coincidencias públicas (`total_count=0`) | Sin evidencia | Sin evidencia | Sin evidencia | No recupera objeto ni contenido | Índice público; negativo reproducible | Una búsqueda vacía no demuestra que el objeto no exista en repositorios no públicos o no indexados. |
| Identificador exacto `f058…` en issues públicos | [GitHub issue search](https://api.github.com/search/issues?q=%22f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4%22) | Sin coincidencias públicas (`total_count=0`) | Sin evidencia | Sin evidencia | Sin evidencia | Ninguna relación establecida | Índice público; negativo reproducible | Issues no son un registro normativo constitutivo; ausencia de hit no prueba ausencia de evidencia. |
| Lectura directa de la ruta local esperada en GitHub | [raw file URL](https://raw.githubusercontent.com/guarnieriagustincyber/TALOS/HEAD/docs/A_PRE_0_BASELINE_SPEC.md), [GitHub contents API](https://api.github.com/repos/guarnieriagustincyber/TALOS/contents/docs/A_PRE_0_BASELINE_SPEC.md) | No se recuperaron bytes; endpoint raw devolvió 404 y API no pudo resolver el repo | Sin evidencia | Sin evidencia | Sin evidencia | No comparables los bytes con el snapshot | Primaria si disponible; no accesible por estas rutas | 404 ambiguo; no permite concluir que el archivo esté ausente del entorno privado original. |
| Lookup de commit/blob exacto usando `f058…` en el repositorio solicitado | [GitHub commit object API](https://api.github.com/repos/guarnieriagustincyber/TALOS/git/commits/f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4), [GitHub blob API](https://api.github.com/repos/guarnieriagustincyber/TALOS/git/blobs/f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4) | El lookup no verificó un objeto (`404`) | Sin evidencia | Sin evidencia | Sin evidencia | Sin evidencia | Primaria si el repo/objeto fueran accesibles | Como el propio repositorio no es públicamente accesible en esas URLs, el 404 no prueba que el objeto esté ausente de la fuente original. |
| Búsqueda literal exacta del hash en código público indexado | GitHub Code Search global, consulta del SHA completo; además búsqueda scoped a `guarnieriagustincyber/TALOS` y a `A_PRE_0_BASELINE_SPEC` | Sin coincidencias devueltas | Sin evidencia | Sin evidencia | Sin evidencia | Sin evidencia | Índice público, únicamente como descubrimiento | El resultado de code search no es exhaustivo ni demuestra ausencia; la búsqueda scoped no pudo confirmar accesibilidad del repo. |
| Designación equivalente y cadena de autoridad | No se encontró fuente primaria pública utilizable en las rutas/repositorios consultados; la búsqueda general no produjo resultados verificables | No identificada | No demostrada | No demostrado | No demostrado | No vinculada al overlay requerido | No hay evidencia positiva | La búsqueda pública acotada no permite descartar registros privados o fuentes oficiales no indexadas. |

Las consultas al perfil público y su lista de repositorios sólo aportaron
contexto sobre recursos públicos visibles; no contienen una designación de
baseline y no se usan para inferir autoridad.

## D. Resultado de las tres rutas

### Ruta A — recuperación directa del artefacto

```text
F058_STATUS = NOT_RECOVERED
IDENTITY_CONFIRMED = NO
AUTHORITY_CONFIRMED = NO
SCOPE_CONFIRMED = NO
PRECEDENCE_CONFIRMED = NO
SNAPSHOT_RELATION_CONFIRMED = NO
```

El SHA completo no produjo un objeto, bytes o referencia primaria accesibles
en las consultas públicas realizadas. No existe candidato recuperado que
pueda someterse a comparación de contenido, versión, filas o estructura con
las dos copias locales. `NOT_RECOVERED` no equivale a probar inexistencia.

### Ruta B — designación normativa equivalente

```text
EQUIVALENT_DESIGNATION = NOT_FOUND (en fuentes públicas consultadas)
```

No se encontró una declaración verificable de un actor competente que
identifique otro artefacto/version como baseline, delimite su scope y fije
precedencia frente a designaciones concurrentes o anteriores.

### Ruta C — cadena de autoridad

```text
AUTHORITY_CHAIN = NOT_ESTABLISHED
```

No fue posible atribuir una designación a un actor/proceso competente ni
enlazarla con un artefacto, scope, precedencia y snapshot requerido.

## E. Cadena de autoridad

```text
ACTOR/AUTHORITY
  = UNVERIFIED
      → DESIGNATION
        = NOT_FOUND IN PUBLIC SOURCES
            → ARTIFACT
              = f058… REFERENCED LOCALLY, NOT RECOVERED
                  → SCOPE
                    = UNVERIFIED
                        → PRECEDENCE
                          = UNVERIFIED
                              → REQUIRED SNAPSHOT
                                = ledger-declared overlay commit
                                  2b2083795602f9099db43bb7ee35b0c030bdf51b
                                  / tree d7ae2718c0a969fd1cf8eee0678f0d6f209c59a7
                                  but authoritative binding UNVERIFIED
```

La identidad descriptiva del overlay registrada en el ledger no prueba quién
la calificó normativamente ni que `f058…` gobierne ese snapshot.

## F. Gaps restantes

1. **Artefact identity:** bytes o prueba verificable que vincule exactamente
   el artefacto gobernante con el hash/revisión designado.
2. **Authority:** actor o proceso competente y evidencia de su competencia.
3. **Designation:** declaración explícita que designe el artefacto como
   baseline aplicable.
4. **Scope:** alcance normativo de la designación, incluyendo el inventario y
   los outcomes A-PRE-0 relevantes.
5. **Precedence:** regla verificable para resolver designaciones concurrentes
   o posteriores.
6. **Snapshot relation:** vínculo explícito y verificable entre la
   designación/artefacto y el overlay cualificado requerido.

Ninguno de los seis elementos queda demostrado por una coincidencia parcial,
por metadata del ledger o por el mero identificador del repositorio.

## G. Invariantes y límites

```text
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
inventory.frozen = false
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
385 rows = unique
385 global dispositions = UNKNOWN
SCOPE_UNPROVEN = PRESERVED
```

No se modificaron manifest, ledger, baseline specs, `requirements.lock`,
membresías, disposiciones, inventario ni readiness. No se ejecutaron TALOS,
FastAPI, probes, workloads, VM, DB, corpus o modelos. No se crearon packets ni
se adjudicó ninguna superficie.

## H. Próxima acción mínima

```text
NEXT_MINIMAL_ACTION = MANTENER_AUTHORITY_UNRESOLVED_HASTA_DISPONER_DE_FUENTE_PRIMARIA_VERIFICABLE
```

Para reabrir la adjudicación de authority se requiere una referencia primaria
accesible que permita probar los gaps de §F. La búsqueda realizada sólo
establece límites de verificación pública; no autoriza inferir que el
artefacto o la autoridad estén ausentes fuera de esas fuentes.
