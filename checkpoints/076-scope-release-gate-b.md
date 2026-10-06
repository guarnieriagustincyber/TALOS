# Checkpoint 076 — fijación del scope de release para Gate B

## 1. Alcance de la decisión

Esta revisión busca fijar el conjunto de currículos contra el que se evaluará
Gate B y `PRODUCT_COMPLETE`. Es documental y no modifica implementación,
configuración funcional ni estados de gates. Se separan deliberadamente:

- identidad o existencia técnica;
- evidencia de implementación;
- evidencia explícita de intención de release;
- decisión de inclusión/exclusión.

La regla aplicada es que las primeras tres no sustituyen la cuarta. En
particular, perfiles configurados, pruebas, fuentes locales, nombres y
clasificaciones técnicas no se convierten en una decisión de release.

## 2. Fuentes consultadas

- `docs/PLAN_MAESTRO_CIERRE_TALOS.md`, propósito de TALOS, estrategia de
  cierre, sección Gate B y condiciones de salida.
- `checkpoints/073-mapa-maestro-talOS-y-camino-restante.md`, propósito del
  producto y conclusión de que el scope debe fijarse antes del cierre binario.
- `checkpoints/074-criterios-objetivos-product-complete.md`, claims del
  producto y criterio que requiere un conjunto finito de currículos declarado.
- `checkpoints/075-evaluacion-gate-b-evidencia-existente.md`, inventario de
  los cinco perfiles cubiertos por evidencia existente y constatación de que
  el scope de release no estaba fijado.
- `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`, H1–H3 y matriz
  de Gate B.
- `config/notebook_identity_decisions.json`, sólo para distinguir
  identidades técnicas ya clasificadas (canónicas/candidatas, legacy,
  independientes y locales unresolved); su propio propósito es audit-only y
  no otorga identidad de release.

No se ejecutaron pruebas/runtime, no se consultó proveedor y no se inspeccionó
DB/corpus.

## 3. Evidencia de intención encontrada

CP073 describe el producto como un tutor educativo técnico basado en evidencia
para currículo técnico/ciberseguridad. CP074 se refiere a los currículos
“actualmente declarados” y exige que Gate B se cierre sobre un conjunto finito
declarado. El plan maestro y CP075 también requieren un scope explícito, pero
ninguno de esos documentos enumera ese conjunto.

La documentación del diagnóstico nombra cinco currículos/perfiles en pruebas
y pendientes de Gate B; esto describe cobertura técnica, no una selección de
release. La configuración de identidades distingue además currículos
candidatos, scopes legacy, notebooks independientes y scopes locales
unresolved; sus clasificaciones tampoco deciden el release.

**Resultado de procedencia:** no se encontró una designación explícita de
inclusión o exclusión de release para ningún conjunto finito. El propósito
general admite más de una selección razonable y no permite escoger una sin
añadir una decisión humana de producto. No se completa ese vacío por
inferencia.

## 4. Tabla de currículos/perfiles considerados

`UNRESOLVED` significa que las fuentes aportan identidad o información
técnica, pero no una decisión de intención de release. Para los scopes que
no representan un currículo versionado, se indica esa limitación; se
incluyen porque aparecen como posibles notebooks/scopes y no se convierten
por ello en currículos del release.

| Currículo/perfil o scope | Identidad técnica | Evidencia de implementación existente | Evidencia de intención de release | Decisión |
|---|---|---|---|---|
| Fase 0 — Programación y Pensamiento Algorítmico (`fase0-soc`; `roadmap_kasiu_v4_fase0`) | Identidad clasificada como `canonical_roadmap_notebook`, distinta de cualquier alias FADENA. | Perfil en la matriz de cinco perfiles; tests de resolver/prompt y caso parametrizado HTTP/SSE reportados en CP075. | Incluido en el propósito general sólo de forma indirecta; no hay lista normativa de release ni designación individual. | `UNRESOLVED` |
| FADENA Lenguajes 2026 (`fadena-lenguajes`; `fadena_lenguajes_2026`) | Identidad clasificada como `canonical_course_notebook`. | Perfil en matriz de cinco, tests de resolver/prompt y caso HTTP/SSE sintético reportados en CP075. | No hay designación individual de release. La presencia en la matriz de test sólo prueba cobertura de test. | `UNRESOLVED` |
| FADENA Sistemas Operativos II 2026 (`fadena-so2`; `fadena_so2_2026`) | Identidad clasificada como `canonical_course_notebook`, distinta del scope legacy `fadena-so`. | Perfil en matriz de cinco y pruebas de selección de perfil; el diagnóstico lo incluye entre las identidades cuya reconciliación efectiva está pendiente. | No hay designación individual de release. Su uso como ejemplo/currículo técnico no fija alcance. | `UNRESOLVED` |
| FADENA Sistema de Tratamiento de Datos 2026 (`fadena-std`; `fadena_std_2026`) | Identidad clasificada como `canonical_course_notebook`; el diagnóstico advierte que la autoridad del programa detallado aún requiere evidencia. | Perfil en matriz de cinco; tests de perfil; fixture integrada endpoint/retrieval/ACL hasta el prompt, limitada y no generalizable, según CP075 y el diagnóstico. | No hay designación de release. CP074 condiciona expresamente la autoridad a que se incluya, pero no decide si se incluye. | `UNRESOLVED` |
| FADENA Telecomunicaciones 2025 (`fadena-teleco`; `fadena_teleco_2025`) | Identidad clasificada como `canonical_course_notebook`. | Perfil en matriz de cinco, tests de resolver/prompt y caso HTTP/SSE sintético reportados en CP075. | No hay designación individual de release. | `UNRESOLVED` |
| FADENA Sociedad y Estado 2026 (`fadena-sye`; `fadena_sye_2026`) | Catálogo la clasifica como curricular catalogado pero no operativo; la decisión de identidad indica no registrar/activar hasta revisar identidad académica, fuentes, roles y ACL. | Evidencia sólo de catálogo en la decisión de identidad; no está entre los cinco perfiles de la matriz Gate B descrita por CP075. | No hay decisión de inclusión/exclusión de release. “No registrar/activar hasta revisar” no se reinterpreta como exclusión de producto. | `UNRESOLVED` |
| Scope legacy `fadena-prog` | Clasificado como `legacy_distinct_scope`; sin alias declarado ni mapeo curricular en la decisión de identidad. No se trata aquí como currículo identificado. | Identidad legacy registrada según la decisión de identidad; sin evidencia de perfil curricular versionado en las fuentes consultadas. | No hay decisión de que compatibilidad legacy forme parte del release. | `UNRESOLVED` |
| Scope legacy `fadena-so` | Clasificado como `legacy_distinct_scope`; expresamente distinto de `fadena-so2`, sin alias declarado. No se trata aquí como currículo identificado. | Identidad legacy/endpoint independiente según la decisión de identidad; sin evidencia de perfil curricular versionado en las fuentes consultadas. | No hay decisión de que compatibilidad legacy forme parte del release. | `UNRESOLVED` |
| Notebook independiente `NB-CYBERSECURITY-V1` | Clasificado como notebook independiente de seguridad; la decisión de identidad prohíbe mapear su `fadena_v1` genérico a un curso FADENA. | Se documenta identidad y asociaciones en el registro audit-only; no forma parte de la matriz de cinco perfiles de CP075. | El objetivo general menciona ciberseguridad, pero no nombra este notebook como scope de release. No se iguala el claim general con esta identidad concreta. | `UNRESOLVED` |
| Scope temático `NB-SEC-01-C-PTR` | Clasificado como scope de tópico de roadmap/ciberseguridad, no como currículo independiente. La decisión de identidad registra además problemas de scope del benchmark, que no se reevalúan aquí. | Se documentan referencias de roadmap y golden set en la decisión audit-only; ninguna de ellas acredita intención de release. | No hay decisión de que este scope temático integre el release funcional. | `UNRESOLVED` |
| Scopes locales `nb_prog_1` y `nb_prog_basica` | Clasificados `local_custom_scope_unresolved`; no tienen identidad curricular confirmada en la decisión audit-only. | Sólo se documenta su existencia local sin identidad curricular resuelta; no hay evidencia de perfil aceptado en las fuentes de Gate B. | No hay decisión de inclusión; la semejanza nominal con carpetas/temas no acredita currículo ni alias. | `UNRESOLVED` |

Esta tabla delimita lo que las fuentes permiten considerar. No declara que
todos los scopes listados deban incluirse, sean currículos válidos o tengan
implementación aceptada. Tampoco afirma que la lista de identidades técnicas
sea exhaustiva respecto de cualquier instalación o usuario.

## 5. Decisión sobre `fadena-std`

```text
FADENA_STD_TECHNICAL_IDENTITY = canonical_course_notebook
FADENA_STD_RELEASE_SCOPE = DECISION_REQUIRED
```

Las fuentes no proporcionan autoridad humana de producto suficiente para
elegir `INCLUDED` o `EXCLUDED`. La autoridad curricular no demostrada tampoco
resuelve la pertenencia: incluirlo no probaría esa autoridad; excluirlo
requiere decisión explícita y no puede deducirse de ese gap.

Hasta que exista una decisión de scope:

- no se marca `fadena-std` incluido ni excluido;
- no se cambia ni elimina su implementación;
- no se pasa el criterio 5 de Gate B a `NOT_APPLICABLE`;
- si una decisión posterior lo incluye, su autoridad curricular seguirá
  pendiente según CP075;
- si una decisión posterior lo excluye, esa exclusión será de alcance y no
  una afirmación sobre invalidez, falta de implementación o falta de valor del
  currículo.

## 6. Estado del scope antes y después

| Punto | Estado |
|---|---|
| Antes, CP075 | `PRODUCT_SCOPE = NOT_FORMALLY_FIXED`; `FADENA_STD_IN_CONFIRMED_RELEASE_SCOPE = UNDETERMINED`. |
| Resultado de CP076 | Se confirma que las fuentes no contienen la designación finita necesaria; se registra `DECISION_REQUIRED` en vez de resolver por inferencia. |
| Después | El conjunto de release sigue sin poder evaluarse; no hay inclusiones ni exclusiones decididas. Gate B y su estado no cambian. |

Este checkpoint resuelve la pregunta de procedencia —no existe una decisión
explícita en las fuentes consultadas— y detiene la selección sustantiva del
scope a la espera de la decisión humana necesaria. No avanza a reconciliación
de IDs/ACL ni a ejecución de Gate B.

## 7. Impacto exacto sobre los cinco criterios Gate B

Las clasificaciones de evidencia de CP075 no cambian por este checkpoint:

| Criterio Gate B | Estado de evidencia registrado en CP075 | Efecto de no tener scope |
|---|---|---|
| 1. IDs canónicos, aliases y `curriculum_id` | `PARTIAL_EXISTING_EVIDENCE` | No existe denominador finito de identidades que reconciliar. No se ejecuta esa reconciliación en CP076. |
| 2. Roles de fuente y ACL efectiva | `PARTIAL_EXISTING_EVIDENCE` | No se sabe qué scopes deben cubrirse; roles/ACL efectivas permanecen pendientes. |
| 3. Selección de perfil por identidad explícita | `PARTIAL_EXISTING_EVIDENCE` | Las pruebas cubren perfiles concretos, pero no se declara que éstos sean el conjunto de release. |
| 4. Ausencia de contaminación entre currículos | `PARTIAL_EXISTING_EVIDENCE` | No puede definirse la matriz completa de pares/scope vecinos hasta fijar el conjunto. |
| 5. Autoridad curricular de `fadena-std` | `BLOCKED` condicional según CP075 | Sigue sin resolverse si aplica. Sólo una exclusión explícita permitiría `NOT_APPLICABLE`; sólo inclusión explícita activaría la condición de demostrar autoridad para este release. |

Por consiguiente, CP076 no pasa, falla ni vuelve a evaluar ningún criterio de
comportamiento. No declara Gate B cerrado ni `PRODUCT_COMPLETE`.

## 8. Invariantes y no-acciones

- No se ejecutaron TALOS/FastAPI, pruebas, benchmarks, workloads ni proveedores.
- No se inspeccionaron ni modificaron DB/corpus productivos, ACL, registry,
  modelos o índices.
- No se modificó código, configuración funcional, tests, fixtures ni gates.
- No se reabrió CP072 ni se repitió investigación de autoridad externa.
- No se modificaron artefactos A-PRE ni estados A-PRE.
- No se convirtió evidencia de fixture/configuración en una selección de
  release ni se extrapoló a otros currículos.
- Cualquier currículo que quede fuera por una futura decisión se considerará
  **excluido del scope de este release**, no inválido, eliminado ni carente de
  implementación.

## Estado de salida

```text
RELEASE_SCOPE = DECISION_REQUIRED
FADENA_STD_RELEASE_SCOPE = DECISION_REQUIRED
```

Se detiene aquí, conforme a la regla de la directiva: hace falta una decisión
humana explícita que seleccione el conjunto finito de currículos y determine
si `fadena-std` está incluido.
