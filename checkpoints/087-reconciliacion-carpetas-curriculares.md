# CP087 — reconciliación de carpetas curriculares contra las 99 relaciones

## 1. Resultado ejecutivo

La estructura local `fuentes/<notebook_id>/` contiene carpetas para los cinco
scopes. La inspección directa, incluyendo archivos locales ignorados por Git,
encontró 76 entradas PDF. Se calcularon hashes SHA-256 y se cotejaron con
`sources.source_id/sha256` en SQLite usando conexión `mode=ro` y
`PRAGMA query_only=ON`; solo se leyeron los 74 source IDs distintos
correspondientes a esos archivos y al universo CP084. No se leyó contenido de
corpus/chunks ni se ejecutó el sincronizador.

El mapeo físico PDF → source ID es inequívoco por igualdad exacta del hash
completo. Cada uno de los 76 PDF locales tiene una relación técnica en su
propia carpeta. En sentido inverso, 24 de las 99 relaciones existen
técnicamente, pero el PDF de identidad exacta aparece solo en otra carpeta;
75 tienen el PDF en la carpeta del notebook correspondiente. Ninguna relación
es ambigua y no se encontró PDF local sin relación técnica de su carpeta.

```text
FOLDER_EVIDENCE_AVAILABLE = YES

RELATIONS_TOTAL = 99
FOLDER_CONFIRMED = 75
FOLDER_ABSENT = 24
FOLDER_AMBIGUOUS = 0

PDFS_TOTAL = 76
PDFS_WITH_TECHNICAL_RELATION = 76
PDFS_WITHOUT_TECHNICAL_RELATION = 0

CROSS_SCOPE_FOLDER_MISMATCHES = 24
UNRESOLVED_PDF_IDENTITIES = 0

L3_STATUS_CHANGED = NO
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
CRITERION_2 = BLOCKED
```

La evidencia de carpeta apoya intención de organización curricular del
usuario, pero no concede autorización L3 ni determina autoridad académica,
procedencia bibliográfica, permiso legal, edición normativa o validez
institucional.

## 2. Perímetro, método y autoridad de la evidencia

Se inspeccionaron únicamente:

- `fuentes/fase0-soc/`
- `fuentes/fadena-lenguajes/`
- `fuentes/fadena-so2/`
- `fuentes/fadena-std/`
- `fuentes/fadena-teleco/`
- las 99 relaciones del universo ya establecido en CP084/CP085;
- el código estático de [`sync_fuentes.py`](../scripts/sync_fuentes.py), que
  documenta el mapeo por SHA-256 contra `sources` y, si no existe fila
  canónica, el formato `src_<16 primeros caracteres del SHA>`;
- una selección de solo `source_id, sha256` para esos IDs en
  `data/web_state/knowledge_store.db`, en modo SQLite de solo lectura.

Para cada archivo se calculó localmente SHA-256 sobre sus bytes, sin moverlo,
copiarlo, renombrarlo ni convertirlo. Se cotejó el hash completo (no el nombre
parecido) con el hash que la tabla `sources` asigna al `source_id`. El
inventario relacional fue extraído de CP084, conservando las 99 filas sin
agregar o eliminar ninguna.

La carpeta y su ubicación se interpretan como evidencia de organización
intencional del usuario, no como ACL/grant. El source ID y SHA prueban la
identidad de bytes observada respecto del registro local; no autentican autor,
edición publicada ni procedencia externa.

La carpeta de Fase 0 sí está presente en el filesystem. La búsqueda glob
inicial no enumeró parte de los PDFs locales ignorados por Git; el inventario
final procede de recorrido directo de filesystem, no solo del glob ni del
índice Git. Las 76 filas de §3 son el conteo utilizado.

No se ejecutaron TALOS/FastAPI, endpoints, sincronizadores, tests, providers,
benchmarks, workloads ni migraciones. No se modificó DB, ACL, asociaciones,
roles, registry, código, corpus, embeddings o modelos. La violación FK de
CP082 no se reparó ni investigó aquí.

## 3. Inventario de PDFs e identidad de bytes

Cada fila es un archivo físico encontrado. `source_id` se resolvió mediante
coincidencia exacta de SHA-256 con el registro local existente. En todas las
filas `technical notebook_id = folder notebook_id` y existe la relación
correspondiente dentro de las 99 relaciones. Las dos copias con el mismo hash
se conservan como dos rutas físicas, no como dos identidades de fuente.

### Fase 0 — `fase0-soc` (19 PDFs)

| pdf_path | SHA-256 | source_id | relación en carpeta |
|---|---|---|---|
| `fuentes/fase0-soc/Automate the Boring Stuff with Python.pdf` | `a5d156fbb37870989baa8ed25d31925565e25d1d06b38d4e1887e1b9d48f5560` | `src_sweigart_automate_boring_stuff` | Y |
| `fuentes/fase0-soc/Codigo limpio - Robert Cecil Martin.pdf` | `92876e0f2bc22b150756f0845f9945fd3291df3067791627d0392bc34603e67d` | `src_martin_clean_code` | Y |
| `fuentes/fase0-soc/Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf` | `7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a` | `src_kurose_computer_networking` | Y |
| `fuentes/fase0-soc/Computer_Security_Stallings_3rd_Ed.pdf` | `0aa9aa4cc0b23293bf20cb1c6968030220427145008143d39b5963d3724c36b1` | `src_stallings_computer_security` | Y |
| `fuentes/fase0-soc/Data Structures and Algorithms in Python.pdf` | `c96e808d96bf01d6550f8bbb80db81b737e3caf76fafee2c3ff3da38e60967bd` | `src_goodrich_dsa_python` | Y |
| `fuentes/fase0-soc/Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf` | `1217dd5e6038f150f454198b9645b7f4b89929ff88ba3744ca2c446082f4fb47` | `src_joyanes_fundamentos` | Y |
| `fuentes/fase0-soc/GUIA_2025-en procesov2.pdf` | `c04f44efcccf2c7304cc0860fe6039d210a922a596988380c7285d658e66f0c2` | `src-guia-2025-c04f44ef` | Y |
| `fuentes/fase0-soc/Matematicas_Discretas_Rosen_IA_16MB.pdf` | `c8146cecbc5e18f7634f13032b5ddb981566a7bcc5152740e13ec67ecabc5b18` | `src_rosen_matematicas_discretas` | Y |
| `fuentes/fase0-soc/Think_Like_a_Programmer.pdf` | `07e0f6d0fb2497b637565ed52d57a5b9cb3701e29e4e792a130e3b351c1d7306` | `src_spraul_think_like_a_programmer` | Y |
| `fuentes/fase0-soc/algoritmos-y-estructuras-de-datos-en-python-digital.pdf` | `e98da4f1f5374047524fead05bb92ee51e44e1743de0082966b5bef0cd8cfa86` | `src_bel_algoritmos_estructuras_python` | Y |
| `fuentes/fase0-soc/luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf` | `db97c77518c68ce3db19da8f65e9f8dd8f9494fcbba59dddb0ed1796973f7e35` | `src_ramalho_fluent_python` | Y |
| `fuentes/fase0-soc/prog_arboles.pdf` | `241af51b9e0b65944911513384563aca9d2623d7b30e6fa2eb04cc4946d65f4f` | `src_fadena_prog_arboles` | Y |
| `fuentes/fase0-soc/prog_archivos.pdf` | `ead0e969f47d966b7d39ac2c3c814bfd78b0134589b386f427898259eff1b56e` | `src_fadena_prog_archivos` | Y |
| `fuentes/fase0-soc/prog_lineales.pdf` | `d03d7669e19abaccdd331067ddf61d38f3113fe684458cf828a14f4553051145` | `src_fadena_prog_lineales` | Y |
| `fuentes/fase0-soc/prog_punteros.pdf` | `4ece5c39d64e25953bac8df1f096f43df90662970f5e6225a2e7d6daa8dcaf9d` | `src_fadena_prog_punteros` | Y |
| `fuentes/fase0-soc/so_concurrencia.pdf` | `4c38c87d686dcc7d03fcd81f0d75d3b2ed5541e7ca9c95635a786ebdef686d85` | `src_fadena_so_concurrencia` | Y |
| `fuentes/fase0-soc/so_memoria.pdf` | `869c24589732b4392c8ae70be552d0e139cbb408e78400a75e186bb2dff574b2` | `src_fadena_so_memoria` | Y |
| `fuentes/fase0-soc/so_planificacion.pdf` | `26cfba6fe46943b6bc0a054a8e82537a90a0aba2dcab302c27bc09b7b9341744` | `src_fadena_so_planificacion` | Y |
| `fuentes/fase0-soc/so_procesos.pdf` | `4f9413043a5e562d43f59db634d9cae5de231c2c1fdd08d3242c5f76cc4eae20` | `src_fadena_so_procesos` | Y |

### Lenguajes — `fadena-lenguajes` (10 PDFs)

| pdf_path | SHA-256 | source_id | relación en carpeta |
|---|---|---|---|
| `fuentes/fadena-lenguajes/Clase1.pdf` | `349766430b88fc9a81a8ef7a287027248dad670eb93ed5b941960f0775d957d3` | `src_fadena_leng_clase1` | Y |
| `fuentes/fadena-lenguajes/Clase2.pdf` | `ed5eab08cd5282356f35d5aded3a01775eb8771160f6ae338efefa49c6752821` | `src_fadena_leng_clase2` | Y |
| `fuentes/fadena-lenguajes/Clase3LP.pdf` | `115f0bc876b44be8e9deabdd9694b7c40ca4c89f11f6c7241bde42b1cba51777` | `src_115f0bc876b44be8` | Y |
| `fuentes/fadena-lenguajes/Clase4LP.pdf` | `8ac0eed0a6121c6aee735e17a74216b4eac35d23e46fc1799d08693ef3740edf` | `src_8ac0eed0a6121c6a` | Y |
| `fuentes/fadena-lenguajes/GNU-c-language-manual.pdf` | `fa5f80f8da3cb25e9a800636e2c817ba552a902819bcfbd18522fab4ff77aed3` | `src_stallman_gnu_c_manual` | Y |
| `fuentes/fadena-lenguajes/Guia Practica 6.pdf` | `fdc4df20e0f9f99e14873059d77fa4631a0d54e31ac3f8122e3ff49e74145074` | `src_fdc4df20e0f9f99e` | Y |
| `fuentes/fadena-lenguajes/Introduccion-a-la-programacion-en-C.pdf` | `dc44a8665f2b23a6e8ebc148731345f79c0eaf21176d1dc58bd25be46cdd0f24` | `src_marzal_intro_programacion_c` | Y |
| `fuentes/fadena-lenguajes/Manual de referencia de C v1.1.docx.pdf` | `7ba98d836c32fe4bb127a799d643009a46e988329c382e5659cae8fcec219910` | `src_7ba98d836c32fe4b` | Y |
| `fuentes/fadena-lenguajes/Programacion-c-principiantes-gorka-urrutia.pdf` | `776399a65bece93855f803b5e303cda85530f964359d2a673c06a310b6ba4742` | `src_urrutia_programacion_c_principiantes` | Y |
| `fuentes/fadena-lenguajes/Semana06 - Clase 01 - Parte 1.pdf` | `1149ca3399b6dd85649a12534f13ba26d67e7f46776050dd18f01d7f87da1e14` | `src_1149ca3399b6dd85` | Y |

### Sistemas Operativos II — `fadena-so2` (9 PDFs)

| pdf_path | SHA-256 | source_id | relación en carpeta |
|---|---|---|---|
| `fuentes/fadena-so2/Clase1SOII.pdf` | `a92d5b22837a59df053a5f691e34f95713272065cb25b896e48b765e13290e45` | `src_fadena_so2_clase1` | Y |
| `fuentes/fadena-so2/FADENA - SO2 - Unidad 3 - Semana 6 - 2026.pdf` | `0fc90b26953694758e052e1f1bdebed4ef337809a6ab621c59cb9582a370d183` | `src_0fc90b2695369475` | Y |
| `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 4 - 2026.pdf` | `a9a056742dcf69aeb4774425b3b65e3a608c920656a34bd18f0d8670d4507c11` | `src_a9a056742dcf69ae` | Y |
| `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 5 - 2026.pdf` | `d253687930308e418cde029d475f6f3755aab6a576f3dbe26ed1d4e4784de685` | `src_d253687930308e41` | Y |
| `fuentes/fadena-so2/FADENA SO II -  S5-A1 - 2026.pdf` | `e9682dece40b58ab7817e1d7877b032a5df2cc70f6a52d476f751737b4911f74` | `src_e9682dece40b58ab` | Y |
| `fuentes/fadena-so2/FADENA SO II - S6-A1 - 2026 (OBLIGATORIA).pdf` | `f009c4e75f5ca3f2cabb07eaeb5ce577dfaed8a67b0f4facc51d0fa6cb0bbdd7` | `src_f009c4e75f5ca3f2` | Y |
| `fuentes/fadena-so2/Operating Systems - Internals and Design Principles 7th.pdf` | `76e248a62974196882b2d33db346a8efd5b8585e45ad89bb81d4859431858ced` | `src_stallings_os_internals_7ed` | Y |
| `fuentes/fadena-so2/Stallings.William.-.Sistemas.Operativos.5ed.pdf` | `0bc5d20dcc91895f9ce10f47bcbfef19d6a2ed40d43cff9f16c6daaeba0c9d0b` | `src_0bc5d20dcc91895f` | Y |
| `fuentes/fadena-so2/clase2SOII.pdf` | `d3b4fecfde23705065e7f5ab5a3a181b5b44ad22c1d378bffa03d0c10b2f4052` | `src_fadena_so2_clase2` | Y |

### Tratamiento de Datos — `fadena-std` (28 PDFs; 27 hashes)

| pdf_path | SHA-256 | source_id | relación en carpeta |
|---|---|---|---|
| `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales - Presentación.pdf` | `cf46d8f0e018b09eb755a2d985cec3d2e0aa3be0cce435db701176b5219ad94a` | `src_cf46d8f0e018b09e` | Y |
| `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales.pdf` | `7822bc3cef85c7831bd50f5749240e27c81cf23dd2b65876bc1d2c7581288132` | `src_7822bc3cef85c783` | Y |
| `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales - Ejercicios.pdf` | `a01b9809f37fb47b785b234938790347b3013f7a43c64350d36b33d73bd868e5` | `src_a01b9809f37fb47b` | Y |
| `fuentes/fadena-std/1 - Estructuras de Datos.pdf` | `d7ff8399759d387a5cdd6170d7ff6f12e14fe51ab7c4936b99d96c4f5eab7962` | `src_d7ff8399759d387a` | Y |
| `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional - Ejercicios.pdf` | `9e866bf082e52dd7bd618196b8a9bc53b01b9c697939824e6d31dbdf7921c4ac` | `src_9e866bf082e52dd7` | Y |
| `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional - Presentación.pdf` | `d946d1a5a3c321444c17347bd8fd3cb3077ca3d4d7c20125d149f2703b766b61` | `src_d946d1a5a3c32144` | Y |
| `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional.pdf` | `3e2e8abda5f55c17881627c46da8d4f3cea57cd35761cec0b89d77c6d5b537c7` | `src_3e2e8abda5f55c17` | Y |
| `fuentes/fadena-std/1 - SQL Básico - Presentación.pdf` | `755be6c147ddc5ddffafed5f570b62552b72e90eddfe54c95a6e875f546e2362` | `src_755be6c147ddc5dd` | Y |
| `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional - Ejercicios.pdf` | `52ff5ff3e07c1da5f3f2103fc4d812a71d68a358452e056a89ea8095ee81a84e` | `src_52ff5ff3e07c1da5` | Y |
| `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional - Presentación.pdf` | `0960283d5cef8deeb06467b5aaa965fe9d15659696657c49f9ddd4fb05f0fd23` | `src_0960283d5cef8dee` | Y |
| `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional.pdf` | `53ef2a7243ae3f63202148b79663fc8f99b52e52baeb175977e8cc7cc406e454` | `src_53ef2a7243ae3f63` | Y |
| `fuentes/fadena-std/2 - Normalización de Bases de Datos - Ejercicios.pdf` | `6dbdc8e943261fa72af4cbc33997637ea05cd4d1dc9c17cce1c24ea30a2ce4da` | `src_6dbdc8e943261fa7` | Y |
| `fuentes/fadena-std/2 - Normalización de Bases de Datos - Presentación.pdf` | `de275591245abbd3c57b80bb9f09a2574a38816a4bc231acc67ca952474428e3` | `src_de275591245abbd3` | Y |
| `fuentes/fadena-std/2 - Normalización de Bases de Datos.pdf` | `9946be0e7d11161a39271d223801dbf766c345b605e754d45236452cb062d387` | `src_9946be0e7d11161a` | Y |
| `fuentes/fadena-std/3 - SQL Básico.pdf` | `f93b8a264e20359c6d1a06c0239f43c7665f8fd5d3624d20e386d74da97b2664` | `src_f93b8a264e20359c` | Y |
| `fuentes/fadena-std/4 - SQL Básico - Ejercicios.pdf` | `7ec00a3365f208e68ea1b55a2b4807525432e2e1d18f37212c574c929285f4e9` | `src_7ec00a3365f208e6` | Y |
| `fuentes/fadena-std/5- Ejercicios estructuras de datos.pdf` | `3102eb1e89e2229e44371dfd0224b494fba872b1ff1972eb37778b0e9787b6b0` | `src_3102eb1e89e2229e` | Y |
| `fuentes/fadena-std/6 - SQL Básico - Soluciones Ejercicios.pdf` | `f3352475bc0cd360ff25e05d6b8b2e5b4ebce8991f0ea9880bf5064e4e41ba58` | `src_f3352475bc0cd360` | Y |
| `fuentes/fadena-std/6- Ejercicios recursividad.pdf` | `032c52bff94a074377fc397ce6fa2e341457d913cfea84f7da8e8cb1141801c9` | `src_032c52bff94a0743` | Y |
| `fuentes/fadena-std/7 - SQL Básico - Alternativas Entorno Interactivo.pdf` | `56cfdbe35123c49e33500f963498468078d8de075db61860f9d96f5fc4b1ae38` | `src_56cfdbe35123c49e` | Y |
| `fuentes/fadena-std/Fundamentos de bases de datos .pdf` | `5e567f9df7f3ddfbc2fe37c8e8aa8dc30932a6d810283b3347908c3761686af1` | `src_silberschatz_fundamentos_bd` | Y |
| `fuentes/fadena-std/Fundamentos-de-Sistemas-de-Bases-de-Datos.pdf` | `bed831d843c06e759665d125cea5087d5a6f57bfc8b5d8c649047f9b2393dc57` | `src_elmasri_navathe_sistemas_bd` | Y |
| `fuentes/fadena-std/Introducción a los Sistemas de Bases de Datos, 7ma Edición, C. J. Date.pdf` | `da02ac37e324cd4bb3742866f19acdd38d585d1bfa9a7a3937c9523054fd3f92` | `src_date_intro_sistemas_bd_7ed` | Y |
| `fuentes/fadena-std/MercedesMarqués (2011) Bases de datos,1era Edición.pdf` | `6a44b761bfdc367814820dd1ab4391909a01bbd95dd1ac89ce99b78beb06e3e9` | `src_marques_bases_de_datos` | Y |
| `fuentes/fadena-std/Raghu-Ramakrishnan-Johannes-Gehrke-Database-Management-Systems-McGraw-Hill-Education-2018.pdf` | `808ae432589d4ea34c8d4be2bf0944f9150d003fcef169e0a55e4a628b21c462` | `src_ramakrishnan_gehrke_dbms` | Y |
| `fuentes/fadena-std/UNIDAD1.pdf` | `d22e633943c623d208564821444f80af1694d61680ec17e9f7ca7ce3e29da305` | `src_fadena_std_unidad1` | Y |
| `fuentes/fadena-std/UNIDAD1STD.pdf` | `d22e633943c623d208564821444f80af1694d61680ec17e9f7ca7ce3e29da305` | `src_fadena_std_unidad1` | Y — duplicate bytes |
| `fuentes/fadena-std/database-systems-design-implementation-and-management.pdf` | `4990c35d1608dee403d88c0cfdddc58656201b9540729c84db860ad73b637828` | `src_coronel_database_systems_11ed` | Y |

### Telecomunicaciones — `fadena-teleco` (10 PDFs)

| pdf_path | SHA-256 | source_id | relación en carpeta |
|---|---|---|---|
| `fuentes/fadena-teleco/Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf` | `7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a` | `src_kurose_computer_networking` | Y — mismos bytes también en Fase 0 |
| `fuentes/fadena-teleco/Comunicaciones_y_redes.pdf` | `1a4caaa17e620e603b8094e2117ead597cd25ca392f1c419e455a82350e5bdbd` | `src_castro_fusario_comunicaciones_redes` | Y |
| `fuentes/fadena-teleco/Douglas E. Comer - Internetworking with TCP_IP Volume One. 1-Addison-Wesley (2013).pdf` | `f04fee214066e3238a7c2e1db8d71dd10dac6e11b93c0823786506c7971cc51c` | `src_comer_internetworking_tcpip_v1` | Y |
| `fuentes/fadena-teleco/Stallings - Comunicaciones y Redes de Computadores - 7ma edición.pdf` | `b6b9613417b60571a903378310c0b213ee10f18b6252cfbb2bfcdefa905e8a38` | `src_stallings_comunicaciones_redes_7ed` | Y |
| `fuentes/fadena-teleco/Unidad 1 - Infraestructura.pdf` | `f7d3f8520381e15648cc3c00f35f00cb8b5570bae32d60f463a7af8a105e47bf` | `src_fadena_teleco_unidad1` | Y |
| `fuentes/fadena-teleco/Unidad 2 2026.pptx.pdf` | `2f1a5843cd1693bac1c96f8b73cc8e92b75ff32eef48b690ceefc237edaddf7b` | `src_2f1a5843cd1693ba` | Y |
| `fuentes/fadena-teleco/Unidad 3 2026.pptx.pdf` | `da10b53f20f2a6477be12356e40a4f824cf266330855365fdf45af867004695f` | `src_da10b53f20f2a647` | Y |
| `fuentes/fadena-teleco/Unidad 4 2026.pptx.pdf` | `001b27137cf6680c4eb4a9e4716ea208cf9bf362d384785f3ced1cfcd71f775c` | `src_001b27137cf6680c` | Y |
| `fuentes/fadena-teleco/Unidad 5 2026.pptx.pdf` | `11195af8e0f2ef4081371e0a5c7c24435dc9b88e3cd0a7adde4c91293cdc35e1` | `src_11195af8e0f2ef40` | Y |
| `fuentes/fadena-teleco/seguridad-en-redes.pdf` | `3caa27ac33ca3ddae9c05094f4e40b0a2f9a1b424c9f63caba3d402f20396abb` | `src_corletti_seguridad_redes` | Y |

Reconciliación del inventario: 19 + 10 + 9 + 28 + 10 = 76 rutas. `UNIDAD1.pdf`
y `UNIDAD1STD.pdf` son dos rutas del mismo hash y source ID; el PDF de Kurose
es un mismo hash/source ID presente en dos carpetas. Por tanto, hay 74 hashes
distintos/source identities en 76 archivos.

## 4. Clasificación y matriz completa de las 99 relaciones

`FOLDER_CONFIRMED` significa que el SHA-256 del PDF en la carpeta del notebook
coincide exactamente con el SHA-256 del `source_id` de la relación. `FOLDER_ABSENT`
significa que no está en esa carpeta; cuando `PDF_LOCATION` indica otra
carpeta, queda demostrado el mismatch de organización para esa relación. No
implica que el source sea inapropiado ni que deba retirarse.

`source_id` y el SHA asociado identifican el mismo objeto de bytes; las filas
confirmadas remiten a §3 para ruta, nombre y hash completos. En las filas
ausentes, la ruta indicada es el lugar donde sí se encontró el PDF de hash
coincidente.

### SCOPE-01 — `fase0-soc` (26 relaciones)

| notebook_id | source_id | clasificación | PDF_LOCATION |
|---|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | FOLDER_CONFIRMED | `fuentes/fase0-soc/GUIA_2025-en procesov2.pdf` |
| `fase0-soc` | `src_0bc5d20dcc91895f` | FOLDER_ABSENT | `fuentes/fadena-so2/Stallings.William.-.Sistemas.Operativos.5ed.pdf` |
| `fase0-soc` | `src_0fc90b2695369475` | FOLDER_ABSENT | `fuentes/fadena-so2/FADENA - SO2 - Unidad 3 - Semana 6 - 2026.pdf` |
| `fase0-soc` | `src_a9a056742dcf69ae` | FOLDER_ABSENT | `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 4 - 2026.pdf` |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | FOLDER_CONFIRMED | `fuentes/fase0-soc/algoritmos-y-estructuras-de-datos-en-python-digital.pdf` |
| `fase0-soc` | `src_d253687930308e41` | FOLDER_ABSENT | `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 5 - 2026.pdf` |
| `fase0-soc` | `src_e9682dece40b58ab` | FOLDER_ABSENT | `fuentes/fadena-so2/FADENA SO II -  S5-A1 - 2026.pdf` |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | FOLDER_ABSENT | `fuentes/fadena-so2/FADENA SO II - S6-A1 - 2026 (OBLIGATORIA).pdf` |
| `fase0-soc` | `src_fadena_prog_arboles` | FOLDER_CONFIRMED | `fuentes/fase0-soc/prog_arboles.pdf` |
| `fase0-soc` | `src_fadena_prog_archivos` | FOLDER_CONFIRMED | `fuentes/fase0-soc/prog_archivos.pdf` |
| `fase0-soc` | `src_fadena_prog_lineales` | FOLDER_CONFIRMED | `fuentes/fase0-soc/prog_lineales.pdf` |
| `fase0-soc` | `src_fadena_prog_punteros` | FOLDER_CONFIRMED | `fuentes/fase0-soc/prog_punteros.pdf` |
| `fase0-soc` | `src_fadena_so_concurrencia` | FOLDER_CONFIRMED | `fuentes/fase0-soc/so_concurrencia.pdf` |
| `fase0-soc` | `src_fadena_so_memoria` | FOLDER_CONFIRMED | `fuentes/fase0-soc/so_memoria.pdf` |
| `fase0-soc` | `src_fadena_so_planificacion` | FOLDER_CONFIRMED | `fuentes/fase0-soc/so_planificacion.pdf` |
| `fase0-soc` | `src_fadena_so_procesos` | FOLDER_CONFIRMED | `fuentes/fase0-soc/so_procesos.pdf` |
| `fase0-soc` | `src_goodrich_dsa_python` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Data Structures and Algorithms in Python.pdf` |
| `fase0-soc` | `src_joyanes_fundamentos` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf` |
| `fase0-soc` | `src_kurose_computer_networking` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf` |
| `fase0-soc` | `src_martin_clean_code` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Codigo limpio - Robert Cecil Martin.pdf` |
| `fase0-soc` | `src_ramalho_fluent_python` | FOLDER_CONFIRMED | `fuentes/fase0-soc/luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf` |
| `fase0-soc` | `src_rosen_matematicas_discretas` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Matematicas_Discretas_Rosen_IA_16MB.pdf` |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Think_Like_a_Programmer.pdf` |
| `fase0-soc` | `src_stallings_computer_security` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Computer_Security_Stallings_3rd_Ed.pdf` |
| `fase0-soc` | `src_stallings_os_internals_7ed` | FOLDER_ABSENT | `fuentes/fadena-so2/Operating Systems - Internals and Design Principles 7th.pdf` |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | FOLDER_CONFIRMED | `fuentes/fase0-soc/Automate the Boring Stuff with Python.pdf` |

### SCOPE-02 — `fadena-lenguajes` (17 relaciones)

| notebook_id | source_id | clasificación | PDF_LOCATION |
|---|---|---|---|
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Semana06 - Clase 01 - Parte 1.pdf` |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Clase3LP.pdf` |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Manual de referencia de C v1.1.docx.pdf` |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Clase4LP.pdf` |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Clase1.pdf` |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Clase2.pdf` |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | FOLDER_ABSENT | `fuentes/fase0-soc/prog_arboles.pdf` |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | FOLDER_ABSENT | `fuentes/fase0-soc/prog_archivos.pdf` |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | FOLDER_ABSENT | `fuentes/fase0-soc/prog_lineales.pdf` |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | FOLDER_ABSENT | `fuentes/fase0-soc/prog_punteros.pdf` |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Guia Practica 6.pdf` |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | FOLDER_ABSENT | `fuentes/fase0-soc/Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf` |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Introduccion-a-la-programacion-en-C.pdf` |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | FOLDER_ABSENT | `fuentes/fase0-soc/Think_Like_a_Programmer.pdf` |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/GNU-c-language-manual.pdf` |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | FOLDER_ABSENT | `fuentes/fase0-soc/Automate the Boring Stuff with Python.pdf` |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | FOLDER_CONFIRMED | `fuentes/fadena-lenguajes/Programacion-c-principiantes-gorka-urrutia.pdf` |

### SCOPE-03 — `fadena-so2` (14 relaciones)

| notebook_id | source_id | clasificación | PDF_LOCATION |
|---|---|---|---|
| `fadena-so2` | `src_0bc5d20dcc91895f` | FOLDER_CONFIRMED | `fuentes/fadena-so2/Stallings.William.-.Sistemas.Operativos.5ed.pdf` |
| `fadena-so2` | `src_0fc90b2695369475` | FOLDER_CONFIRMED | `fuentes/fadena-so2/FADENA - SO2 - Unidad 3 - Semana 6 - 2026.pdf` |
| `fadena-so2` | `src_a9a056742dcf69ae` | FOLDER_CONFIRMED | `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 4 - 2026.pdf` |
| `fadena-so2` | `src_d253687930308e41` | FOLDER_CONFIRMED | `fuentes/fadena-so2/FADENA - SO2 Unidad 2 - Semana 5 - 2026.pdf` |
| `fadena-so2` | `src_e9682dece40b58ab` | FOLDER_CONFIRMED | `fuentes/fadena-so2/FADENA SO II -  S5-A1 - 2026.pdf` |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | FOLDER_CONFIRMED | `fuentes/fadena-so2/FADENA SO II - S6-A1 - 2026 (OBLIGATORIA).pdf` |
| `fadena-so2` | `src_fadena_so2_clase1` | FOLDER_CONFIRMED | `fuentes/fadena-so2/Clase1SOII.pdf` |
| `fadena-so2` | `src_fadena_so2_clase2` | FOLDER_CONFIRMED | `fuentes/fadena-so2/clase2SOII.pdf` |
| `fadena-so2` | `src_fadena_so_concurrencia` | FOLDER_ABSENT | `fuentes/fase0-soc/so_concurrencia.pdf` |
| `fadena-so2` | `src_fadena_so_memoria` | FOLDER_ABSENT | `fuentes/fase0-soc/so_memoria.pdf` |
| `fadena-so2` | `src_fadena_so_planificacion` | FOLDER_ABSENT | `fuentes/fase0-soc/so_planificacion.pdf` |
| `fadena-so2` | `src_fadena_so_procesos` | FOLDER_ABSENT | `fuentes/fase0-soc/so_procesos.pdf` |
| `fadena-so2` | `src_stallings_computer_security` | FOLDER_ABSENT | `fuentes/fase0-soc/Computer_Security_Stallings_3rd_Ed.pdf` |
| `fadena-so2` | `src_stallings_os_internals_7ed` | FOLDER_CONFIRMED | `fuentes/fadena-so2/Operating Systems - Internals and Design Principles 7th.pdf` |

### SCOPE-04 — `fadena-std` (30 relaciones)

| notebook_id | source_id | clasificación | PDF_LOCATION |
|---|---|---|---|
| `fadena-std` | `src_032c52bff94a0743` | FOLDER_CONFIRMED | `fuentes/fadena-std/6- Ejercicios recursividad.pdf` |
| `fadena-std` | `src_0960283d5cef8dee` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional - Presentación.pdf` |
| `fadena-std` | `src_3102eb1e89e2229e` | FOLDER_CONFIRMED | `fuentes/fadena-std/5- Ejercicios estructuras de datos.pdf` |
| `fadena-std` | `src_3e2e8abda5f55c17` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional.pdf` |
| `fadena-std` | `src_52ff5ff3e07c1da5` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional - Ejercicios.pdf` |
| `fadena-std` | `src_53ef2a7243ae3f63` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Álgebra Relacional y Cálculo Relacional.pdf` |
| `fadena-std` | `src_56cfdbe35123c49e` | FOLDER_CONFIRMED | `fuentes/fadena-std/7 - SQL Básico - Alternativas Entorno Interactivo.pdf` |
| `fadena-std` | `src_6dbdc8e943261fa7` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Normalización de Bases de Datos - Ejercicios.pdf` |
| `fadena-std` | `src_755be6c147ddc5dd` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - SQL Básico - Presentación.pdf` |
| `fadena-std` | `src_7822bc3cef85c783` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales.pdf` |
| `fadena-std` | `src_7ec00a3365f208e6` | FOLDER_CONFIRMED | `fuentes/fadena-std/4 - SQL Básico - Ejercicios.pdf` |
| `fadena-std` | `src_9946be0e7d11161a` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Normalización de Bases de Datos.pdf` |
| `fadena-std` | `src_9e866bf082e52dd7` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional - Ejercicios.pdf` |
| `fadena-std` | `src_a01b9809f37fb47b` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales - Ejercicios.pdf` |
| `fadena-std` | `src_cf46d8f0e018b09e` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Diseño de Bases de Datos Relacionales - Presentación.pdf` |
| `fadena-std` | `src_coronel_database_systems_11ed` | FOLDER_CONFIRMED | `fuentes/fadena-std/database-systems-design-implementation-and-management.pdf` |
| `fadena-std` | `src_d7ff8399759d387a` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Estructuras de Datos.pdf` |
| `fadena-std` | `src_d946d1a5a3c32144` | FOLDER_CONFIRMED | `fuentes/fadena-std/1 - Fundamentos del Modelo Relacional - Presentación.pdf` |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | FOLDER_CONFIRMED | `fuentes/fadena-std/Introducción a los Sistemas de Bases de Datos, 7ma Edición, C. J. Date.pdf` |
| `fadena-std` | `src_de275591245abbd3` | FOLDER_CONFIRMED | `fuentes/fadena-std/2 - Normalización de Bases de Datos - Presentación.pdf` |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | FOLDER_CONFIRMED | `fuentes/fadena-std/Fundamentos-de-Sistemas-de-Bases-de-Datos.pdf` |
| `fadena-std` | `src_f3352475bc0cd360` | FOLDER_CONFIRMED | `fuentes/fadena-std/6 - SQL Básico - Soluciones Ejercicios.pdf` |
| `fadena-std` | `src_f93b8a264e20359c` | FOLDER_CONFIRMED | `fuentes/fadena-std/3 - SQL Básico.pdf` |
| `fadena-std` | `src_fadena_prog_archivos` | FOLDER_ABSENT | `fuentes/fase0-soc/prog_archivos.pdf` |
| `fadena-std` | `src_fadena_std_unidad1` | FOLDER_CONFIRMED | `fuentes/fadena-std/UNIDAD1.pdf`; `UNIDAD1STD.pdf` tiene el mismo SHA |
| `fadena-std` | `src_marques_bases_de_datos` | FOLDER_CONFIRMED | `fuentes/fadena-std/MercedesMarqués (2011) Bases de datos,1era Edición.pdf` |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | FOLDER_CONFIRMED | `fuentes/fadena-std/Raghu-Ramakrishnan-Johannes-Gehrke-Database-Management-Systems-McGraw-Hill-Education-2018.pdf` |
| `fadena-std` | `src_ramalho_fluent_python` | FOLDER_ABSENT | `fuentes/fase0-soc/luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf` |
| `fadena-std` | `src_rosen_matematicas_discretas` | FOLDER_ABSENT | `fuentes/fase0-soc/Matematicas_Discretas_Rosen_IA_16MB.pdf` |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | FOLDER_CONFIRMED | `fuentes/fadena-std/Fundamentos de bases de datos .pdf` |

### SCOPE-05 — `fadena-teleco` (12 relaciones)

| notebook_id | source_id | clasificación | PDF_LOCATION |
|---|---|---|---|
| `fadena-teleco` | `src-guia-2025-c04f44ef` | FOLDER_ABSENT | `fuentes/fase0-soc/GUIA_2025-en procesov2.pdf` |
| `fadena-teleco` | `src_001b27137cf6680c` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Unidad 4 2026.pptx.pdf` |
| `fadena-teleco` | `src_11195af8e0f2ef40` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Unidad 5 2026.pptx.pdf` |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Unidad 2 2026.pptx.pdf` |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Comunicaciones_y_redes.pdf` |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Douglas E. Comer - Internetworking with TCP_IP Volume One. 1-Addison-Wesley (2013).pdf` |
| `fadena-teleco` | `src_corletti_seguridad_redes` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/seguridad-en-redes.pdf` |
| `fadena-teleco` | `src_da10b53f20f2a647` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Unidad 3 2026.pptx.pdf` |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Unidad 1 - Infraestructura.pdf` |
| `fadena-teleco` | `src_kurose_computer_networking` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf` |
| `fadena-teleco` | `src_stallings_computer_security` | FOLDER_ABSENT | `fuentes/fase0-soc/Computer_Security_Stallings_3rd_Ed.pdf` |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | FOLDER_CONFIRMED | `fuentes/fadena-teleco/Stallings - Comunicaciones y Redes de Computadores - 7ma edición.pdf` |

## 5. Resumen por notebook y PDFs sin relación

| notebook_id | relaciones técnicas | confirmadas por carpeta | ausentes | ambiguas | PDFs de carpeta |
|---|---:|---:|---:|---:|---:|
| `fase0-soc` | 26 | 19 | 7 | 0 | 19 |
| `fadena-lenguajes` | 17 | 10 | 7 | 0 | 10 |
| `fadena-so2` | 14 | 9 | 5 | 0 | 9 |
| `fadena-std` | 30 | 27 | 3 | 0 | 28 |
| `fadena-teleco` | 12 | 10 | 2 | 0 | 10 |
| **TOTAL** | **99** | **75** | **24** | **0** | **76** |

`PDFS_WITH_TECHNICAL_RELATION = 76`: cada ruta PDF tiene por lo menos una
relación `notebook_id → source_id` en la carpeta que la contiene.
`PDFS_WITHOUT_TECHNICAL_RELATION = 0`. No se añade una relación por el hecho
de que un PDF exista; la afirmación describe únicamente que la asociación ya
está presente en el universo histórico. Los duplicados físicos no aumentan el
conteo de source identities: hay 74 hashes distintos.

## 6. Relaciones sin respaldo local y cruces de scope

Las 24 relaciones `FOLDER_ABSENT` se listan íntegramente abajo. En cada caso
el hash del PDF correspondiente sí fue localizado en la carpeta indicada, y
la relación técnica aparece para el notebook de destino; por eso las 24
cuentan como `CROSS_SCOPE_FOLDER_MISMATCHES`. El conteo es por relación, no
por número de source IDs únicos.

| notebook_id de la relación | source_id | carpeta donde está el PDF coincidente | resultado |
|---|---|---|---|
| `fase0-soc` | `src_0bc5d20dcc91895f` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_0fc90b2695369475` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_a9a056742dcf69ae` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_d253687930308e41` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_e9682dece40b58ab` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fase0-soc` | `src_stallings_os_internals_7ed` | `fadena-so2` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-so2` | `src_fadena_so_concurrencia` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-so2` | `src_fadena_so_memoria` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-so2` | `src_fadena_so_planificacion` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-so2` | `src_fadena_so_procesos` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-so2` | `src_stallings_computer_security` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-std` | `src_fadena_prog_archivos` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-std` | `src_ramalho_fluent_python` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-std` | `src_rosen_matematicas_discretas` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-teleco` | `src-guia-2025-c04f44ef` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |
| `fadena-teleco` | `src_stallings_computer_security` | `fase0-soc` | `TECHNICAL_RELATION_WITHOUT_FOLDER_SUPPORT` |

### Multi-scope con respaldo físico en cada scope

`src_kurose_computer_networking` está asociado en `fase0-soc` y
`fadena-teleco`. El mismo SHA-256
`7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a` aparece
en las dos carpetas bajo el mismo nombre de PDF. Se clasifica como
`INTENTIONAL_MULTI_SCOPE_CANDIDATE`: la presencia duplicada es compatible con
intención de inclusión en ambos cuadernos, no demuestra autorización ni
pertinencia.

Otros shared sources aparecen en la carpeta de uno de los scopes pero no en
la otra. Se cuentan en la tabla anterior como discrepancias de respaldo local,
no se consideran automáticamente contaminación ni se clasifican como
rechazados. Las asociaciones cross-scope no se borran ni se heredan.

## 7. Tratamiento específico de `fadena-std`

Se conserva la decisión `FADENA_STD_RELEASE_SCOPE = INCLUDED`. Para STD, 27 de
30 relaciones tienen un PDF con SHA coincidente dentro de `fuentes/fadena-std`.
Tres asociaciones (`src_fadena_prog_archivos`, `src_ramalho_fluent_python` y
`src_rosen_matematicas_discretas`) no tienen allí su PDF; sus bytes coinciden
con PDFs que están en `fuentes/fase0-soc`.

Esto respalda que esos archivos están organizados bajo Fase 0 y no bajo la
carpeta STD observada. No resuelve, rechaza ni revoca la relación técnica de
STD. Se mantienen intactos los estados de CP085:

| source_id de STD | estado C4-DRAFT previo | observación de carpeta en CP087 |
|---|---|---|
| `src_ramakrishnan_gehrke_dbms` | `POLICY_DECISION_PENDING` | PDF exacto en carpeta STD; no se convierte en grant. |
| `src_f3352475bc0cd360` | `PEDAGOGICAL_USE_PENDING` | PDF exacto en carpeta STD; no resuelve el tratamiento de soluciones ni uso. |
| `src_fadena_prog_archivos` | `UNRESOLVED`; procedencia/archivo de curso no demostrados en STD | PDF exacto solo en carpeta Fase 0; no se atribuye a STD. |
| `src_ramalho_fluent_python` | `UNRESOLVED`; evidencia curricular/procedencia incompleta | PDF exacto solo en carpeta Fase 0; no se atribuye a STD. |
| `src_rosen_matematicas_discretas` | `UNRESOLVED`; pertenencia/bibliografía/procedencia no confirmadas | PDF exacto solo en carpeta Fase 0; no se atribuye a STD. |

Para `src_ramakrishnan_gehrke_dbms`, `src_f3352475bc0cd360` y los otros casos,
el match de hash demuestra identidad física local y ubicación, no firma,
procedencia bibliográfica o autoridad externa.

## 8. Qué demuestra y qué no demuestra la carpeta

La evidencia obtenida permite afirmar, para este checkout/corte:

- qué carpetas existen para los cinco IDs;
- qué PDFs hay dentro de ellas, con sus rutas y hashes exactos;
- qué registros `source_id` tienen identidad de bytes coincidente;
- qué relaciones del universo ya establecido cuentan con un PDF físico en su
  carpeta esperada;
- qué relaciones técnicas carecen de ese soporte local, aunque el PDF exista
  en otra carpeta;
- el único caso observado de un mismo hash localizado en ambos scopes con
  relación en ambos: Kurose (`INTENTIONAL_MULTI_SCOPE_CANDIDATE`).

No demuestra por sí sola:

- autorización L3, ACL, propósito permitido ni decisor;
- autoridad académica/institucional externa;
- procedencia bibliográfica, autenticidad o permiso legal;
- que las fuentes en la carpeta sean curricularmente apropiadas;
- que el contenido de los PDFs se haya ingerido íntegramente o esté vigente;
- que la organización de archivos local represente otros despliegues;
- que una relación sin PDF local deba eliminarse, o que un PDF sin relación
  debiera agregarse.

## 9. Reconciliación con CP084–086 y estado de Gate B

El universo sigue siendo exactamente el de CP084–086: 99 relaciones, por
notebook `26 + 17 + 14 + 30 + 12`. CP087 no recalcula ni reemplaza la
adjudicación L3. La evidencia de carpetas se puede usar en una futura
construcción/validación del manifiesto como evidencia de intención e identidad
física, manteniendo separados `EXISTING_EVIDENCE` y cualquier
`CURRENT_RELEASE_AUTHORIZATION`.

El estado normativo queda:

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0
C2_AUTHORIZATION_THRESHOLD = L3
CRITERION_2 = BLOCKED
L3_STATUS_CHANGED = NO
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
```

## Cierre obligatorio

```text
FOLDER_EVIDENCE_AVAILABLE = YES

RELATIONS_TOTAL = 99
FOLDER_CONFIRMED = 75
FOLDER_ABSENT = 24
FOLDER_AMBIGUOUS = 0

PDFS_TOTAL = 76
PDFS_WITH_TECHNICAL_RELATION = 76
PDFS_WITHOUT_TECHNICAL_RELATION = 0

CROSS_SCOPE_FOLDER_MISMATCHES = 24
UNRESOLVED_PDF_IDENTITIES = 0

L3_STATUS_CHANGED = NO
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
CRITERION_2 = BLOCKED
```
