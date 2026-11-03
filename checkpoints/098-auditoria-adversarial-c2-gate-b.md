# CP098 — AUDITORÍA ADVERSARIAL DE C2 (GATE B)

## 1. Identidad de la auditoría

```text
CP = 098
GATE = B (Identidad y aislamiento curricular)
CRITERION = C2 (Roles de fuente y ACL efectiva)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor técnico adversarial y ejecutor de evidencia
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → CLASSIFY → DOCUMENT
```

---

## 2. Marco contractual y normativo

* **CP074 §5:** Define el Criterio 2 como `REQUIRED_FOR_PRODUCT`:
  > *"Roles de fuente y ACL efectiva consistentes desde selección hasta retrieval y prompt. Condición objetiva de cierre: En casos positivos sólo se seleccionan/evidencian fuentes autorizadas; en negativos/out-of-scope ninguna fuente no autorizada alcanza el prompt/resultado y se observa la respuesta de límite prevista."*
* **CP083:** Estableció el estándar uniforme de autorización documental:
  > *"L3 = estándar de autorización de fuentes para el release (decisión documental explícita, trazable, con scope, source, identidad/versión, propósito, decisor y efecto autorizante)."*
* **CP084–CP086:** Inventariaron las 99 relaciones `notebook_id → source_id` y concluyeron `0/99 L3 DEMONSTRATED` (84 evidencia parcial, 15 sin evidencia localizada).
* **CP088–CP092:** Fijaron el modelo relacional (identidad global, `NATIVE`/`REUSED`, roles semánticos independientes de la función curricular, y política D3-C que permite `FADENA → SOC` como complementario y deja `SOC → FADENA` fuera de la política).
* **CP093:** Determinó que las 20 relaciones nativas no requieren forzar `curricular_function` para Gate B, y que las 17 relaciones `SOC → FADENA` representan `RELATION_OUTSIDE_CURRENT_RELEASE_POLICY` (no rechazo normativo, pero sin grant positivo concedido).
* **CP097:** Cerró formalmente `C1 = PASS` sobre provisioning limpio determinista. CP098 asume la identidad curricular como premisa resuelta y evalúa estrictamente las fuentes y su ACL.

---

## 3. Inventario completo y reconciliado de las 99 relaciones

Las 99 relaciones persistidas en el release scope se distribuyen en los 5 cuadernos:

### 3.1 `fase0-soc` (26 relaciones)

| # | `source_id` | Pertenencia | Rol declarado (`U`) | Función curricular | Estado Política D3-C | Estado Autorización L3 | Allowlist técnica |
|---|---|---|---|---|---|---|---|
| 1 | `src-guia-2025-c04f44ef` | `REUSED` (home: teleco) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 2 | `src_0bc5d20dcc91895f` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 3 | `src_0fc90b2695369475` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 4 | `src_a9a056742dcf69ae` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 5 | `src_bel_algoritmos_estructuras_python` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 6 | `src_d253687930308e41` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 7 | `src_e9682dece40b58ab` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 8 | `src_f009c4e75f5ca3f2` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 9 | `src_fadena_prog_arboles` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 10 | `src_fadena_prog_archivos` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 11 | `src_fadena_prog_lineales` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 12 | `src_fadena_prog_punteros` | `NATIVE` | `IMPLEMENTATION, REFERENCE` | `NOT_ESTABLISHED` (D4) | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 13 | `src_fadena_so_concurrencia` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 14 | `src_fadena_so_memoria` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 15 | `src_fadena_so_planificacion` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 16 | `src_fadena_so_procesos` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 17 | `src_goodrich_dsa_python` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 18 | `src_joyanes_fundamentos` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 19 | `src_kurose_computer_networking` | `REUSED` (home: teleco) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 20 | `src_martin_clean_code` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 21 | `src_ramalho_fluent_python` | `NATIVE` | `—` | `COMPLEMENTARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 22 | `src_rosen_matematicas_discretas` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 23 | `src_spraul_think_like_a_programmer` | `NATIVE` | `METHODOLOGICAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 24 | `src_stallings_computer_security` | `NATIVE` | `—` | `COMPLEMENTARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 25 | `src_stallings_os_internals_7ed` | `REUSED` (home: so2) | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 26 | `src_sweigart_automate_boring_stuff` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` (Nativa) | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |

### 3.2 `fadena-lenguajes` (17 relaciones)

| # | `source_id` | Pertenencia | Rol declarado (`U`) | Función curricular | Estado Política D3-C | Estado Autorización L3 | Allowlist técnica |
|---|---|---|---|---|---|---|---|
| 27 | `src_1149ca3399b6dd85` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 28 | `src_115f0bc876b44be8` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 29 | `src_7ba98d836c32fe4b` | `NATIVE` | `REFERENCE` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 30 | `src_8ac0eed0a6121c6a` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 31 | `src_fadena_leng_clase1` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 32 | `src_fadena_leng_clase2` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 33 | `src_fadena_prog_arboles` | `REUSED` (home: soc) | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 34 | `src_fadena_prog_archivos` | `REUSED` (home: soc) | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 35 | `src_fadena_prog_lineales` | `REUSED` (home: soc) | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 36 | `src_fadena_prog_punteros` | `REUSED` (home: soc) | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 37 | `src_fdc4df20e0f9f99e` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 38 | `src_joyanes_fundamentos` | `REUSED` (home: soc) | `PRIMARY, METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 39 | `src_marzal_intro_programacion_c` | `NATIVE` | `METHODOLOGICAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 40 | `src_spraul_think_like_a_programmer` | `REUSED` (home: soc) | `METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 41 | `src_stallman_gnu_c_manual` | `NATIVE` | `REFERENCE` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 42 | `src_sweigart_automate_boring_stuff` | `REUSED` (home: soc) | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 43 | `src_urrutia_programacion_c_principiantes` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |

### 3.3 `fadena-so2` (14 relaciones)

| # | `source_id` | Pertenencia | Rol declarado (`U`) | Función curricular | Estado Política D3-C | Estado Autorización L3 | Allowlist técnica |
|---|---|---|---|---|---|---|---|
| 44 | `src_0bc5d20dcc91895f` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 45 | `src_0fc90b2695369475` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 46 | `src_a9a056742dcf69ae` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 47 | `src_d253687930308e41` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 48 | `src_e9682dece40b58ab` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 49 | `src_f009c4e75f5ca3f2` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 50 | `src_fadena_so2_clase1` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 51 | `src_fadena_so2_clase2` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 52 | `src_fadena_so_concurrencia` | `REUSED` (home: soc) | `PRIMARY, METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 53 | `src_fadena_so_memoria` | `REUSED` (home: soc) | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 54 | `src_fadena_so_planificacion` | `REUSED` (home: soc) | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 55 | `src_fadena_so_procesos` | `REUSED` (home: soc) | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 56 | `src_stallings_computer_security` | `REUSED` (home: soc) | `IMPLEMENTATION` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 57 | `src_stallings_os_internals_7ed` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |

### 3.4 `fadena-std` (30 relaciones)

| # | `source_id` | Pertenencia | Rol declarado (`U`) | Función curricular | Estado Política D3-C | Estado Autorización L3 | Allowlist técnica |
|---|---|---|---|---|---|---|---|
| 58 | `src_032c52bff94a0743` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 59 | `src_0960283d5cef8dee` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 60 | `src_3102eb1e89e2229e` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 61 | `src_3e2e8abda5f55c17` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 62 | `src_52ff5ff3e07c1da5` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 63 | `src_53ef2a7243ae3f63` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 64 | `src_56cfdbe35123c49e` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 65 | `src_6dbdc8e943261fa7` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 66 | `src_755be6c147ddc5dd` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 67 | `src_7822bc3cef85c783` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 68 | `src_7ec00a3365f208e6` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 69 | `src_9946be0e7d11161a` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 70 | `src_9e866bf082e52dd7` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 71 | `src_a01b9809f37fb47b` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 72 | `src_cf46d8f0e018b09e` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 73 | `src_coronel_database_systems_11ed` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 74 | `src_d7ff8399759d387a` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 75 | `src_d946d1a5a3c32144` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 76 | `src_date_intro_sistemas_bd_7ed` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 77 | `src_de275591245abbd3` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 78 | `src_elmasri_navathe_sistemas_bd` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 79 | `src_f3352475bc0cd360` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 80 | `src_f93b8a264e20359c` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 81 | `src_fadena_prog_archivos` | `REUSED` (home: soc) | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 82 | `src_fadena_std_unidad1` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 83 | `src_marques_bases_de_datos` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 84 | `src_ramakrishnan_gehrke_dbms` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 85 | `src_ramalho_fluent_python` | `REUSED` (home: soc) | `IMPLEMENTATION` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 86 | `src_rosen_matematicas_discretas` | `REUSED` (home: soc) | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 87 | `src_silberschatz_fundamentos_bd` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |

### 3.5 `fadena-teleco` (12 relaciones)

| # | `source_id` | Pertenencia | Rol declarado (`U`) | Función curricular | Estado Política D3-C | Estado Autorización L3 | Allowlist técnica |
|---|---|---|---|---|---|---|---|
| 88 | `src-guia-2025-c04f44ef` | `REUSED` (home: soc) | `METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 89 | `src_001b27137cf6680c` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 90 | `src_11195af8e0f2ef40` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 91 | `src_2f1a5843cd1693ba` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 92 | `src_castro_fusario_comunicaciones_redes` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 93 | `src_comer_internetworking_tcpip_v1` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 94 | `src_corletti_seguridad_redes` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 95 | `src_da10b53f20f2a647` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 96 | `src_fadena_teleco_unidad1` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 97 | `src_kurose_computer_networking` | `NATIVE` | `PRIMARY, METHODOLOGICAL` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 98 | `src_stallings_computer_security` | `REUSED` (home: soc) | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |
| 99 | `src_stallings_comunicaciones_redes_7ed` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | `L3_NOT_DEMONSTRATED` | `TECHNICALLY_ALLOWED` |

---

## 4. Estado de autorización L3 y provenance

```text
RELATIONS_TOTAL = 99
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0
AUTHORIZATION_PROVENANCE_STATUS = NOT_DEMONSTRATED
```

* **Hallazgo documental:** No existe en el repositorio ningún documento o artefacto trazable que emita una aprobación positiva (grant) conforme al estándar L3 aceptado en CP083.
* **Separación de planos:**
  * La presencia física del PDF en carpetas no otorga autorización L3.
  * La persistencia en la tabla `notebook_sources` prueba asociación técnica previa, no aprobación normativa.
  * La declaración de roles en `config/notebook_source_roles.json` es configuración descriptiva, no un grant formal.

---

## 5. Arquitectura del camino técnico de ACL y flujo de recuperación

Se inspeccionó de extremo a extremo la ruta real de ejecución en `src/study_engine/web/routes/chat.py` y `src/study_engine/storage/knowledge_store.py`:

```text
1. Solicitud de Chat
   ↓ (target_notebook_id)
2. Resolución de Allowlist en chat.py:
   _authorized_sources_for_scope() ejecuta:
   SELECT DISTINCT source_id FROM notebook_sources WHERE notebook_id IN (?)
   ↓ (scope_source_ids = 100% dependiente de la tabla notebook_sources)
3. Filtrado opcional de usuario:
   _filter_requested_sources() (si active_sources=None, conserva todo scope_source_ids)
   ↓ (retrieval_source_ids)
4. Búsqueda léxica aislada en KnowledgeStore.search():
   SELECT c.id, c.document_id, c.source_id, -bm25(chunks_fts) AS score ...
   FROM chunks_fts
   JOIN chunks c ON c.rowid = chunks_fts.rowid
   JOIN notebook_sources ns ON ns.source_id = c.source_id
   WHERE chunks_fts MATCH ? AND ns.notebook_id = ?
   ↓ (search_results)
5. Filtro post-búsqueda en chat.py:
   search_results = [res for res in search_results if res.source_id in retrieval_source_ids]
   ↓
6. Expansión greedy por ventana en SectionExpander:
   expander.expand_results(seed_results)
   ↓
7. Empaquetado contextual epistémico:
   final_formatted = expanded_context_text if expanded_context_text else "\n\n".join(citations_formatted)
   EpistemicContextPack(formatted_context=final_formatted)
   ↓
8. Prompt final al LLM:
   Inyección directa de pack.formatted_context en el prompt de inferencia.
```

---

## 6. Efecto real de los roles de fuente

Se verificó el impacto operacional de los roles declarados en `config/notebook_source_roles.json`:

1. **En `KnowledgeStore.search()`:**
   * La consulta SQL realiza un `JOIN notebook_sources ns ON ns.source_id = c.source_id WHERE ns.notebook_id = ?`.
   * **No consulta roles ni filtra por rol.**
   * El ranking es `-bm25(chunks_fts)` puro. No aplica pesos de autoridad (`authority_matrix_ref`).
2. **En `chat.py` (Endpoint principal):**
   * La allowlist no consulta roles.
   * `resolve_epistemic_role()` utiliza listas hardcodeadas de autores en `structured_pipeline.py`, independientes de `notebook_source_roles.json`, únicamente para asignar la etiqueta `"epistemic_role"` en la metadata del chunk para la UI.
3. **En `MultiSourceEvidenceAssembler`:**
   * Agrupa citas en cubos semánticos (`PRIMARY`, `METHODOLOGICAL`, etc.) para el orquestador pedagógico al resolver KCs, pero no gobierna el endpoint general de chat.
4. **Conclusión:**
   ```text
   ROLE_EFFECT = METADATA_ONLY
   ```
   Los roles no restringen la allowlist técnica ni modulan el ranking de retrieval en runtime.

---

## 7. Resultados de las pruebas de ejecución adversarial (Harness sintético)

Se ejecutó el harness técnico [`scratch/audit_c2.py`](file:///home/agustin/.gemini/antigravity/brain/31012c01-9fec-4c0a-9023-331ef1196c87/scratch/audit_c2.py) sobre almacenamiento limpio en memoria:

### A. Aislamiento técnico directo entre cuadernos (Notebook Isolation)
* **Escenario:** `nb_a` asociado a `src_a`; `nb_b` asociado a `src_b`.
* **Resultado:**
  * Búsqueda en `nb_a` recupera únicamente `src_a` (1 hit).
  * Búsqueda en `nb_a` por términos exclusivos de `src_b` retorna 0 hits.
  * Búsqueda en `nb_b` recupera únicamente `src_b` (1 hit).
* **Veredicto:** `CROSS_SOURCE_BYPASS = NOT_OBSERVED_IN_DIRECT_SEARCH`. El `JOIN notebook_sources` previene el cruce accidental no declarado entre cuadernos.

### B. Vulnerabilidad de frontera en `SectionExpander` (Adversarial Bypass)
* **Escenario:** Un documento `doc_shared` contiene el Chunk 1 (`pos_index=1`, perteneciente a `src_allowed`) y el Chunk 2 (`pos_index=2`, perteneciente a `src_unauthorized`). Se consulta el cuaderno con `seed_hits` conteniendo únicamente el Chunk 1.
* **Mecanismo:** `SectionExpander.expand_results` ejecutó:
  ```sql
  SELECT id, document_id, source_id, content, page_start, pos_index, section, token_count
  FROM chunks
  WHERE document_id = ? AND pos_index BETWEEN ? AND ?
  ORDER BY pos_index ASC;
  ```
* **Observación empírica:** `SectionExpander` recuperó ambos chunks (`expanded_chunks count = 2`).
  * Fuentes presentes en la expansión: `{'src_allowed', 'src_unauthorized'}`.
  * El texto de `src_unauthorized` ingresó directamente en `expanded_context_text` y por ende en el prompt.
* **Veredicto:**
  ```text
  SECTION_EXPANSION_BYPASS = OBSERVED
  ```
  `SectionExpander` carece de filtro SQL `AND source_id IN (retrieval_source_ids)` y no reintersecta sus resultados expandidos con la allowlist de fuentes permitidas.

### C. Discrepancia de Política: 17 Relaciones SOC → FADENA
* **Escenario:** Las 17 relaciones `SOC → FADENA` están fuera de la cobertura de la política curricular D3-C (`POLICY_NOT_GRANTED`) y carecen de autorización L3 (`L3_NOT_DEMONSTRATED`).
* **Comportamiento en código:** En la base de datos de desarrollo y en cualquier instalación que replique `notebook_sources`, estas 17 relaciones están asociadas en la tabla `notebook_sources`.
* **Observación empírica:** `_authorized_sources_for_scope()` las selecciona en `retrieval_source_ids`. Son `TECHNICALLY_ALLOWED` en runtime por el backend de chat.
* **Veredicto:** La allowlist técnica actual no valida la política de reutilización D3-C ni la autorización L3.

---

## 8. Verificación de integridad de la base de datos de desarrollo

```text
PRE_HASH  = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
POST_HASH = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
PRE_MTIME = 1790366294.078985 (2026-09-25 16:58:14.078985 -0300)
POST_MTIME = 1790366294.078985 (2026-09-25 16:58:14.078985 -0300)

DATABASE_CHANGES = 0 (INTACTA)
```

---

## 9. Verificación de estado Git

```bash
git diff --check   # Retorna 0 (limpio)
git status --short # Cero modificaciones no autorizadas en código o tests
```

* `TECHNICAL_SOURCE_CHANGES = 0` (harness de prueba ejecutado desde el scratchpad).
* `DATABASE_CHANGES = 0`.

---

## 10. Adjudicación formal de C2

Conforme a la metodología y al estándar vinculante L3:

```text
C2_CONTRACTUAL_STATUS = BLOCKED
C2_AUTHORIZATION_STATUS = NOT_DEMONSTRATED (0/99 L3)
C2_TECHNICAL_ACL_STATUS = PARTIAL (ALLOWLIST_UNVALIDATED_AND_EXPANDER_BYPASS_OBSERVED)
C2_CERTIFICATION = BLOCKED
NATURE = ASSURANCE_BLOCKER
```

### Fundamentación del bloqueo:
1. **Déficit de autorización L3 (`0/99`):** Ninguna de las 99 relaciones cuenta con un acto documental de aprobación positiva que satisfaga el estándar L3 aceptado en CP083.
2. **Desalineación de allowlist frente a política D3-C:** 17 relaciones `SOC → FADENA` que carecen de cobertura positiva bajo D3-C son tratadas como `TECHNICALLY_ALLOWED` por la consulta cruda a `notebook_sources` en el endpoint de chat.
3. **Falta de restricción estructural en `SectionExpander`:** Se comprobó experimentalmente que `SectionExpander` consulta fragmentos vecinos por `document_id` sin reintersectar contra la allowlist autorizada (`SECTION_EXPANSION_BYPASS = OBSERVED`), permitiendo filtraciones en documentos multi-fuente.

---

## 11. Resumen maestro formal vigente de Gate B (C1–C5 post-CP098)

| Criterio Gate B | Estado vigente | Naturaleza del estado | Evidencia faltante para cierre |
|---|---|---|---|
| **C1 — IDs, aliases y `curriculum_id`** | **`PASS`** | `CLOSED` | Criterio cerrado definitivamente en CP097. |
| **C2 — Roles de fuente y ACL efectiva** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Actos de autorización L3 (0/99), alineación de allowlist con D3-C y blindaje de SectionExpander. |
| **C3 — Selección de prompt/perfil** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Test integrado request → resolver → prompt para los 5 currículos declarados. |
| **C4 — Aislamiento multi-currículo** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Suite/matriz versionada de no-contaminación (rutas positivas y negativas). |
| **C5 — Autoridad de `fadena-std`** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Documento de programa académico oficial verificable o decisión de exclusión. |

```text
GATE_B_FORMAL_BLOCKERS = [C2, C5]
GATE_B_PENDING_ASSURANCE = [C3, C4]
GATE_B_CLOSED_CRITERIA = [C1]
```

---

## 12. Regla de continuidad y próximo paso

* **C1 permanece cerrado (`PASS / CLOSED`).** No se reabre.
* **C2 queda formalmente dictaminado como `BLOCKED / ASSURANCE_BLOCKER`.**
* **Acciones mínimas requeridas para resolver el bloqueo de C2:**
  1. **Decisión humana / Acto documental L3:** Formalizar el manifiesto de autorización de fuentes para el release scope (CP086) mediante aprobación explícita de las relaciones destinadas a producción.
  2. **Resolución de la política D3-C sobre las 17 relaciones `SOC → FADENA`:** Decidir formalmente si se conceden, se excluyen de la allowlist técnica o se restringen.
  3. **Blindaje técnico de `SectionExpander`:** Agregar en su consulta SQL o en su lógica de filtrado la verificación explícita `source_id IN (retrieval_source_ids)`.
