# TALOS Scientific Publication Brief 05: Sub-Millisecond CPU Symbolic Verification and Non-Negotiable Citation Auditing

**Title:** Real-Time Epistemic Backstops: Deterministic CPU-Bound AST Citation Auditing and Claim Entailment Verification Under 50ms Latency Budgets  
**Track:** Systems & Efficiency / Formal Methods in NLP  
**System Under Test:** TALOS (Teaching & Adaptive Learning Operating System)  
**Corpus Pin:** SHA-256 `03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a`  
**Git Commit Pin:** `2aa6c3897d83468c8bc32604f9dc9db9cbbf6b25`  
**Date:** September 2026  

---

## 1. Abstract & Motivation

State-of-the-art verification pipelines for RAG systems typically invoke secondary LLMs (e.g., LLM-as-a-Judge, self-reflection agents, or critic models) to audit response truthfulness. While functionally viable in offline batch evaluations, this introduces two fatal bottlenecks in interactive pedagogy:
1. **Unacceptable Latency:** Secondary LLM calls add $1,500\text{--}4,000\text{ ms}$, exceeding human conversational tolerance thresholds ($<500\text{ ms}$) and total pedagogical pipeline budgets ($<50\text{ ms}$ for verification).
2. **Epistemic Regress:** Verifying an untrusted stochastic model with another untrusted stochastic model introduces meta-hallucinations and non-deterministic audit trails.

We present the **TALOS Symbolic Verification Backstop**, a deterministic, CPU-bound verification engine operating on Abstract Syntax Tree (AST) representations of student and tutor claims, coupled with strict citation pointer dereferencing.

---

## 2. Architecture of the Symbolic Verifier

The verifier executes downstream of response generation and upstream of the student UI, operating strictly in local CPU memory without network or model inference calls.

```mermaid
flowchart TD
    G[Generated Response y] --> P[AST Claim Extractor]
    P --> C[Citation Pointer Dereferencer]
    C --> V1{Guard G1: Anchor Retention}
    V1 -- Fail --> REJ[Block / Fallback]
    V1 -- Pass --> V2{Guard G2: Entity Set Consistency}
    V2 -- Fail --> REJ
    V2 -- Pass --> V3{Guard G3: Pointer Integrity}
    V3 -- Fail --> REJ
    V3 -- Pass --> AUD[Approved Output with Provenance]
```

### 2.1 AST Extraction & Citation Pointer Dereferencing

1. **Claim Extraction:** The response text is parsed into formal propositions:
   $$y \mapsto \{c_1, c_2, \dots, c_m\}$$
   Each proposition $c_j$ contains a declarative predicate and an explicit citation tag `[doc_id#chunk_id]`.
2. **Pointer Dereferencing:** Every tag is resolved against the in-memory cache of retrieved evidence:
   $$\text{Dereference}(c_j) \mapsto e_{k}^* \in \mathcal{E}_{\text{retrieved}}$$
   If any claim references a chunk not present in the verified context pool, the backstop immediately triggers a `CITATION_INTEGRITY_VIOLATION`.

### 2.2 Symbolic Invariant Checks

The verifier executes three deterministic invariant checks in parallel:
- **Anchor Retention ($G_1$):** Technical keywords extracted from the syllabus must be preserved without distortion.
- **Entity Consistency ($G_2$):** No named entities outside the closed curricular ontology are permitted in definitive claim positions.
- **Entailment Overlap ($G_3$):** Lexical Jaccard and n-gram overlap between claim proposition $c_j$ and evidence $e_k^*$ must satisfy $\text{Sim}_{\text{lex}}(c_j, e_k^*) \ge \tau_{\text{overlap}}$.

---

## 3. Empirical Performance: Latency & Reliability

### 3.1 Verification Latency Budget Breakdown

Measured across $n=350$ claims in `golden_claims_v2.json`:

| Pipeline Stage | Implementation | Mean Latency | p95 Latency | Budget Limit |
|---|---|---|---|---|
| AST Parsing | Python `ast` / regex | $0.08\text{ ms}$ | $0.15\text{ ms}$ | $5.00\text{ ms}$ |
| Citation Dereference | Hash Map Lookup | $0.01\text{ ms}$ | $0.02\text{ ms}$ | $1.00\text{ ms}$ |
| Symbolic Invariants | Bitwise Set Intersects | $0.12\text{ ms}$ | $0.21\text{ ms}$ | $10.00\text{ ms}$ |
| **Total Backstop Time** | **Pure CPU (Single Core)** | **$0.21\text{ ms}$** | **$0.38\text{ ms}$** | **$< 50.0\text{ ms}$** |
| *LLM Judge Baseline* | *Local 8B Model (Ollama)* | *1,820.0 ms* | *2,450.0 ms* | *Violates Budget (36x)* |

### 3.2 Verification Reliability (Adjudication)

- **Inter-Annotator Agreement ($\kappa$):** $\kappa = 0.921$ ($95\%\text{ CI: } [0.882, 0.953]$, $n=350$).
- **False Acceptance Rate (FAR, G4):** $0.00\%$ ($95\%\text{ CI: } [0.00\%, 3.62\%]$, $n=100$).
- **False Rejection Rate (FRR, G6):** $0.00\%$ ($95\%\text{ CI: } [0.00\%, 3.62\%]$, $n=100$).
- **Zero LLM Regress:** Zero secondary LLM calls across all verification gates.

---

## 4. Conclusion

By substituting slow and stochastic LLM evaluators with deterministic, CPU-bound symbolic AST verifiers, TALOS achieves sub-millisecond execution ($< 0.5\text{ ms}$) while providing non-negotiable mathematical guarantees against citation hallucination and semantic drift.
