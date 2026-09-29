# A-2 — Reproducibility precheck

**Outcome:** consolidated clean-environment PRE **ESTABLISHED** after A-1
through A-5 for the exact checkout delta recorded below. This is reproducibility
evidence, not product/release certification. The initial run and its database
write remain documented as historical incident evidence.

## Initial checkout reference

| Field | Value |
|---|---|
| HEAD | `b2f02122caf80dffcd98cfb212752ed34dce41b2` |
| Checkout | Dirty; the A-1 changes and A-2 dependency changes were not committed. |
| Initial-run delta | 8 tracked modified, 0 staged, 4 untracked. |
| Platform | Linux `7.0.0-34-generic` / glibc 2.39 / x86_64 |

The initial gate ran against the working tree at that HEAD, not against a clean
commit. Those counts identify the earlier snapshot, before test-isolation
changes; the exact delta for the final successful run is recorded below.

## Dependency contract

- Declarative authority: `pyproject.toml`.
- `requirements.lock`: generated with `uv pip compile --all-extras
  --generate-hashes --python-version 3.10`.
- Resolver: `uv 0.12.20`.
- All 61 locked packages resolved and synced successfully, including `dev`,
  `gate2-diagnostics`, `experiments`, and `local-inference`.
- Lock SHA-256:
  `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`.
- Regeneration was repeated with the same uv version and command; the before
  and after lock SHA-256 values matched exactly.
- `requirements.txt` is explicitly marked as a deprecated, partial
  compatibility file, not a supported installation path.

The clean installation exposed two undeclared dependencies:

1. `python-multipart`, required when FastAPI registers the file-upload routes.
2. `onnxruntime` and `tokenizers`, needed by the ONNX local inference tests and
   local model backend.

These are now declared as runtime (`python-multipart`) or the
`local-inference` extra. The ONNX-related test failures from the first clean
attempt were not suppressed: after adding the extra, all 31 focused
embedding/reranker/relevance-gate tests passed. The first full-gate attempt
before that extra had 2,809 passed, 6 failed, and 5 errors; failures were
associated with the missing ONNX/tokenizer runtime and the simulated fallback.

## Initial clean environment evidence

| Check | Result |
|---|---|
| Temporary environment | `/tmp/talos-a2-clean.YegEYt` (outside the repository; did not reuse or modify `.venv`). |
| Python | 3.12.3 |
| `sys.executable` | `/tmp/talos-a2-clean.YegEYt/bin/python` |
| Lock sync | PASS |
| Editable package install | PASS, `--no-deps --no-build-isolation` after lock sync |
| `pip check` | PASS — no broken requirements |
| Runtime, web, LLM, local inference, diagnostics, and experiment smoke imports | PASS |
| Focused ONNX/retrieval tests | 31 passed |
| Release quality gate | 2,820 passed, 0 failed, 147 warnings in 408.10 s |
| External live/network tests | Explicitly `NOT RUN`, per A-1 perimeter |

The release gate was invoked explicitly with the temporary interpreter:
`/tmp/talos-a2-clean.YegEYt/bin/python -m scripts.quality_gate --profile release`.

## Protected-data comparison

Hashes below were captured before the first full clean-gate attempt and after
the final full clean-gate run. There was an intervening failed full-gate
attempt before adding `local-inference`, so the comparison covers the complete
test-run sequence. The vector-store database is the exception.

| Artifact | Before | After | Result |
|---|---|---|---|
| `data/eval/golden_set_v2_400.json` | `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1` | same | unchanged |
| `data/eval/golden_set_v2_400.meta.json` | `29ca0ff25563d739fb45fb83e7507ced85e13ba7cfdede6bbd52c8439a5bb9ca` | same | unchanged |
| `data/eval/qrels/golden_set_v2_400.qrels.json` | `68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc` | same | unchanged |
| `data/eval/golden_set_v2_401.json` | `4442e267f5c5eddb778fa2f36065db4841a8c221fbc4ee7a12aa8513ef844857` | same | unchanged |
| `data/eval/golden_set_v2_401.meta.json` | `086220f1680e45afebd5b0a1b7ba4196eefdda56eb99dda1effca5767d6bcf66` | same | unchanged |
| `data/eval/qrels/golden_set_v2_401.qrels.json` | `a76b18d6b113b164c3e68455577bfea8777789af4efb179464ad1d8be87d32e6` | same | unchanged |
| `data/web_state/knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | same | unchanged |
| `src/study_engine/diagnostics/gate2_evidence_relations.py` | `d7ac608502fbbda0a4d50c55825b310210c3bc027f0d2a1cb745773ce270bd60` | same | unchanged |
| `tests/protected/manifest.json` | `d5d992d8edae5bd707a2970b461926978a7c79069468611e40042ddca30f0661` | same | unchanged |
| `data/web_state/vector_store.db` | `8926128d7cc47af9fb2b676d92c245cbe38032cdc3eefe44e53c48a594aa2177` | `b0e665856e824f441944de8eaea7d8678de1cc0fadfb9e72711dd85e026ca322` | **changed** |

The vector database size remained 1,369,837,568 bytes. A read-only
`PRAGMA integrity_check` after the run returned `ok`, and its current journal
mode is `wal`. The original pre-run file is no longer available, so its change
cannot be declared harmless or reverted from this evidence. No restore or
overwrite was attempted.

## Writer isolation follow-up

A later staged experiment on temporary copies localized the write:

1. Constructing `SQLiteVectorStore` and initializing its schema did not change
   the copied main database hash.
2. `AppContainer` calls `StudyLoopExperimentRunner.initialize_pipeline()`,
   which calls `SQLiteVectorStore.save_records()` for the six vectors indexed
   from `prog_punteros.pdf`.
3. All six records already existed and their compared field values and vector
   blobs were identical. The `INSERT OR REPLACE` still wrote a 16,512-byte WAL;
   the warmup did not increase it. Closing/checkpointing the connection changed
   the copied main-file hash.
4. Read-only SQL comparison found no added, removed, or value-different rows.
   This establishes a physical rewrite of logically identical rows in the
   experiment, not byte identity with the unavailable historical file.

The write was therefore in the runtime initialization path invoked by tests,
not the scheduled web retrieval warmup. Tests that need the populated web
state now receive a verified session-scoped copy of both databases through
`web_state_test_copy`; other test containers already use temporary working
directories. The focused affected set passed (51 tests), and the active
databases retained their hashes across that run:

| Artifact | Hash before | Hash after | Result |
|---|---|---|---|
| `knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | same | unchanged |
| `vector_store.db` | `b0e665856e824f441944de8eaea7d8678de1cc0fadfb9e72711dd85e026ca322` | same | unchanged |

This focused validation does not replace a new full release-gate run from a
clean environment. The historical vector-store hash
`8926128d7cc47af9fb2b676d92c245cbe38032cdc3eefe44e53c48a594aa2177` remains
unavailable and must not be redefined as if it had been restored.

The release profile was then rerun with the repository `.venv` (not a clean
external environment). It completed with **2,819 passed, 1 failed, 146
warnings**. The only failure was
`test_numpy_blas_performance_scale`: its 1,000-vector timing was 437.91 ms
against a 100 ms threshold. Running that test alone still measured 184.65 ms;
with `OPENBLAS_NUM_THREADS=1`, it passed in 0.13 s. This points to BLAS
threading/environment sensitivity in that performance check, not a failure in
the database isolation change. No change was made to that unrelated test.
Both protected database hashes were identical before and after the full run.

## Final clean rerun after isolation

The release gate was repeated after isolating web-state tests. This used a new
external virtualenv; neither the checkout `.venv` nor the earlier temporary
environment was reused.

| Check | Final result |
|---|---|
| Checkout HEAD | `b2f02122caf80dffcd98cfb212752ed34dce41b2` |
| Checkout state | Dirty; 17 tracked modified, 5 untracked; no staged changes |
| Tracked diff SHA-256 | `66cbdc7e22e657e8667449fe22517af5717ac12ddba957e60e563bb89ca2e68f` |
| Other untracked files SHA-256 | `f4e1382c6ef582f91effa883ca41698421e7d2d66c7b08278d7e6be95f032e64` |
| Python | 3.12.3 |
| Executable | `/tmp/talos-a2-clean-final.W6fhrk/bin/python` |
| Platform | Linux `7.0.0-34-generic`, glibc 2.39, x86_64 |
| Lock resolver | `uv 0.12.20` |
| Lock SHA-256 | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Lock sync / editable install | PASS; all 61 locked packages synced, editable install used `--no-deps --no-build-isolation` |
| `pip check` | PASS — no broken requirements |
| Runtime, web, LLM, local inference, diagnostics, experiment imports | PASS |
| BLAS environment | `OPENBLAS_NUM_THREADS=1` |
| Release gate | **2,820 passed, 0 failed, 147 warnings, 401.01 s** |
| External live/network tests | Explicitly `NOT RUN`, as required by the release profile |

The gate command was invoked directly with the external interpreter:
`OPENBLAS_NUM_THREADS=1 /tmp/talos-a2-clean-final.W6fhrk/bin/python -m scripts.quality_gate --profile release`.
The BLAS thread count was controlled rather than changing the existing
performance threshold; the earlier 100 ms failure without that setting and
the isolated success with one thread are retained above as environment
sensitivity evidence.

The untracked-files digest above is the SHA-256 of sorted `sha256sum` records
for the other untracked files; it excludes this report to avoid a self-
referential fingerprint. Together with the tracked diff digest and HEAD, it
identifies the source delta used by this final run.

| Protected artifact | SHA-256 before | SHA-256 after | Result |
|---|---|---|---|
| `data/web_state/knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | same | unchanged |
| `data/web_state/vector_store.db` | `b0e665856e824f441944de8eaea7d8678de1cc0fadfb9e72711dd85e026ca322` | same | unchanged |

Neither database had a WAL file before or after the gate. The historical
vector-store hash `8926128d7cc47af9fb2b676d92c245cbe38032cdc3eefe44e53c48a594aa2177`
remains unavailable; this run validates invariance from the current known
state and does not claim restoration of the historical file.

## Decision

- **Dependency declaration/lock:** PASS.
- **Clean environment reconstruction:** PASS in the final external virtualenv.
- **Release gate on the existing `.venv`:** FAIL, 2,819 passed and 1
  performance-threshold failure; this was not a clean-environment rerun.
- **Protected-data invariance in the original clean-gate run:** FAIL for
  `vector_store.db`; cause localized to duplicate vector replacement during
  runtime initialization.
- **Focused isolation remediation:** PASS; 51 affected tests passed against a
  temporary database copy and active database hashes remained unchanged.
- **Protected-data invariance in the latest full run:** PASS; both active
  database hashes remained unchanged.
- **Final clean release gate:** PASS, 2,820 passed, 0 failed; BLAS threading
  controlled with `OPENBLAS_NUM_THREADS=1`.
- **Final protected-data invariance:** PASS; active database hashes unchanged.
- **A-2:** **CLOSED** for dependency/lock reconstruction and release-gate
  reproducibility under the recorded checkout, platform, and environment.
- **PRE:** **ESTABLISHED** for that exact local checkout delta and environment.
- **Product/release certification:** **NOT ESTABLISHED** by this PRE.

## Consolidated PRE after A-3/A-4/A-5

After the later A-3 benchmark metric correction, A-4 CLI BKT error handling,
and A-5 README inventory update, the release profile was rerun from another
fresh external environment. This is the consolidated PRE for the current
Ola 0.5 local delta; it supersedes the earlier 2,820-test run for current
readiness, while preserving that earlier evidence above.

| Check | Consolidated result |
|---|---|
| Checkout HEAD | `b2f02122caf80dffcd98cfb212752ed34dce41b2` |
| Checkout | Dirty; 22 tracked modified, 6 untracked, 0 staged |
| Tracked diff SHA-256 | `909b5faaeeb6b713f60633c913cf8cbf5f79de39dbba47d94f5e1e9b67b31fa1` |
| Other untracked files SHA-256 | `0b971ed78283267d0bd06f2280d4741f8b3bafab6cfc9b24b5dd7c15ef421bae` |
| Python / executable | 3.12.3 / `/tmp/talos-ola05-final.92tNR8/bin/python` |
| Platform | Linux `7.0.0-34-generic`, glibc 2.39, x86_64 |
| Resolver / lock SHA-256 | `uv 0.12.20` / `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Lock sync, editable install, `pip check` | PASS; all 61 packages synced, editable install used `--no-deps --no-build-isolation`, no broken requirements |
| Critical imports | PASS for runtime, web, LLM, diagnostics and all declared extras |
| BLAS setting | `OPENBLAS_NUM_THREADS=1` |
| Release gate | **2,831 passed, 0 failed, 147 warnings, 425.14 s** |
| Inventory | 447 `test_*.py` files across 24 suites; the A-3 addition contributes 6 collected metric cases and A-4 adds 5 CLI/storage cases |
| Live/network overrides | `NOT RUN`, explicitly optional in the perimeter |

Command:
`OPENBLAS_NUM_THREADS=1 /tmp/talos-ola05-final.92tNR8/bin/python -m scripts.quality_gate --profile release`.
The new state was measured at `HEAD` plus the tracked diff and untracked-file
fingerprints above. This report's consolidated-result text is appended after
the run and is excluded from those fingerprints; it is documentation-only and
does not change the code/tests measured by the gate.

| Protected artifact | SHA-256 before | SHA-256 after | Result |
|---|---|---|---|
| `knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | same | unchanged |
| `vector_store.db` | `b0e665856e824f441944de8eaea7d8678de1cc0fadfb9e72711dd85e026ca322` | same | unchanged |
| `golden_set_v2_400.json` | `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1` | same | unchanged |
| `golden_set_v2_401.json` | `4442e267f5c5eddb778fa2f36065db4841a8c221fbc4ee7a12aa8513ef844857` | same | unchanged |
| `golden_set_v2_400.qrels.json` | `68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc` | same | unchanged |
| `golden_set_v2_401.qrels.json` | `a76b18d6b113b164c3e68455577bfea8777789af4efb179464ad1d8be87d32e6` | same | unchanged |
| `tests/protected/manifest.json` | `d5d992d8edae5bd707a2970b461926978a7c79069468611e40042ddca30f0661` | same | unchanged |
| `gate2_evidence_relations.py` | `d7ac608502fbbda0a4d50c55825b310210c3bc027f0d2a1cb745773ce270bd60` | same | unchanged |

No `knowledge_store.db-wal` or `vector_store.db-wal` sidecar existed before or
after the run. The unrecoverable historical vector DB hash
`8926128d7cc47af9fb2b676d92c245cbe38032cdc3eefe44e53c48a594aa2177` remains
historical evidence only; the invariant established here is current-state
before equals current-state after.

**Consolidated decision:** A-1 through A-5 are implemented for this local
Ola 0.5 delta; A-2 dependency reconstruction is reproducible; the consolidated
release test gate passes and the checked protected artifacts remain invariant.
PRE is established only for the exact checkout delta, lock, Linux/x86_64
platform, Python version and BLAS configuration above. Optional live/network
tests were not run. **This does not establish product certification, release
certification, BENCH-G2 canonicality, or recovery of the historical database.**
