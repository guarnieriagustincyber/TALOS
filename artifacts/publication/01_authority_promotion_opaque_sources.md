# TALOS Scientific Publication Brief 01: Authority Promotion Over Opaque Curricular Sources

**Title:** Beyond Heuristic OCR Recovery: Deterministic Authority Promotion and Multi-Tier Canonicalization in Technical Pedagogy Corpora  
**Track:** Information Retrieval / Epistemic Systems Engineering  
**System Under Test:** TALOS (Teaching & Adaptive Learning Operating System)  
**Corpus Pin:** SHA-256 `03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a` (31,173 chunks, 27 sources)  
**Git Commit Pin:** `2aa6c3897d83468c8bc32604f9dc9db9cbbf6b25`  
**Date:** September 2026  

---

## 1. Abstract & Motivation

In curricular and safety-critical technical education (e.g., Computer Systems Architecture, Operating Systems, Cryptography), naive Retrieval-Augmented Generation (RAG) fails catastrophically when dealing with heterogeneous coursepacks, scanned slides, and legacy PDFs. The core pathology lies in the false conflation:
$$\text{SOURCE EXISTS} \implies \text{RETRIEVABLE} \implies \text{SUPPORTS CLAIM} \implies \text{TRUSTED}$$

Standard dense or lexical retrievers treat all chunks matching query tokens with equal epistemic weight. In practice, scanned textbooks subject to optical character recognition (OCR) degradation produce garbled tokens, fragmented syntax, and spurious overlaps. We demonstrate a deterministic, zero-LLM architecture that enforces a strict Epistemic Hierarchy via the **Authority Promotion Operator** and Multi-Tier Canonical Arbitration (CAL).

---

## 2. Theoretical Formulation: The Epistemic Dissociation

Let a pedagogical collection $\mathcal{C}$ consist of documents $d \in \mathcal{C}$ partitioned into curricular authority tiers:
1. $\mathcal{T}_{\text{primary}}$: Authoritative textbooks, frozen syllabi, formal normative specifications ($\text{weight } w_{\text{auth}} = 1.0$).
2. $\mathcal{T}_{\text{secondary}}$: Lab workbooks, instructional notes, vetted slide transcriptions ($w_{\text{auth}} = 0.75$).
3. $\mathcal{T}_{\text{external}}$: Auxiliary references, external threat intelligence, student submissions ($w_{\text{auth}} \le 0.50$).

We formally repudiate the naive implication chain by establishing four distinct predicates for any claim $c$ and retrieved chunk $e$:

1. **Existence:** $\mathcal{E}(e) \triangleq e \in \mathcal{C}$.
2. **Retrievability:** $\mathcal{R}(e, q) \triangleq \text{score}(e, q) \ge \tau_{\text{retrieval}}$.
3. **Claim Support (Entailment):** $\mathcal{S}(e, c) \triangleq \text{Entails}(e, c) \wedge \neg \text{Contradicts}(e, c)$.
4. **Epistemic Trust (Authority):** $\mathcal{T}(e) \triangleq \text{Tier}(e) \succeq \text{Tier}_{\text{req}}(c) \wedge \text{QualityScore}(e) \ge \tau_{\text{quality}}$.

Therefore:
$$\mathcal{E}(e) \not\implies \mathcal{R}(e, q) \not\implies \mathcal{S}(e, c) \not\implies \mathcal{T}(e)$$

### 2.1 The Authority Promotion Operator

Given candidate chunks $\{e_i\}_{i=1}^k$ retrieved for query $q$, the ranking score $S(e_i, q)$ is not a pure function of semantic cosine similarity or BM25/FTS5 rank. Instead, it is governed by the deterministic monotonic promotion function:

$$S_{\text{promoted}}(e_i, q) = \Phi(e_i) \cdot \left[ \alpha \cdot \text{RRF\_Score}(e_i, q) + \beta \cdot \text{LexicalScore}(e_i, q) \right]$$

where:
- $\Phi(e_i) = w_{\text{auth}}(\text{Tier}(e_i)) \cdot (1 - \lambda \cdot \mathbb{I}_{\text{degraded}}(e_i))$
- $\mathbb{I}_{\text{degraded}}(e_i) = 1$ if OCR character error rate $\text{CER}(e_i) > \tau_{\text{ocr}}$ or heading hierarchy is malformed; $0$ otherwise.
- In cross-namespace federation, sort tie-breaking strictly adheres to:
  $$\text{SortKey}(e_i) = \left( -w_{\text{auth}}(e_i), \; \text{doc\_id}(e_i), \; \text{chunk\_id}(e_i) \right)$$
  guaranteeing zero directional bias and strictly deterministic ordering ($p95 < 0.1\text{ ms}$).

---

## 3. Handling Opaque and Degraded Sources (CAL Engine)

To resolve conflicts between primary opaque sources (e.g., scanned legacy PDFs) and secondary digital materials without invoking non-deterministic LLMs:
1. **Deterministic Probing:** Chunks are pre-screened with `conversion_probe.py` using invariant hash checks.
2. **Canonical Arbitration:** When primary and secondary chunks present lexical or structural conflicts:
   - Primary source is retained as canonical unless secondary digital text exceeds primary by margin $\delta_{\text{canon}} \ge +0.15$ with stability margin $\varepsilon \le \pm 0.02$.
   - Conflict exposure rate is strictly monitored ($\tau_{\text{conflict}} = 0.12$). In TALOS testbeds, $4/45$ conflicts ($8.89\%$) were exposed; zero were smoothed or averaged out.

---

## 4. Empirical Evaluation on Real Corpus

- **Corpus Size:** 31,173 chunks, 27 sources, $60.2\text{ MB}$ SQLite FTS5 store.
- **Dataset:** `queries_expanded_v2.json` ($n=195$), `golden_claims_v2.json` ($n=350$).
- **Statistical Results:**
  - Cohen's Kappa on epistemic adjudication: $\kappa = 0.921$ ($95\%\text{ CI: } [0.882, 0.953]$), passing the $\kappa \ge 0.85$ bound.
  - False Acceptance Rate (FAR, G4): $0.00\%$ ($95\%\text{ CI: } [0.00\%, 3.62\%]$, $n=100$), rigorously promoted from conditional.
  - False Rejection Rate (FRR, G6): $0.00\%$ ($95\%\text{ CI: } [0.00\%, 3.62\%]$, $n=100$), rigorously promoted from conditional.
  - Unwarranted Claim Rate Critical (UCR-crit, G5a): $0.00\%$ ($95\%\text{ CI: } [0.00\%, 7.11\%]$, $n=50$).

---

## 5. Conclusion

Treating document retrieval as an unweighted similarity contest creates catastrophic epistemic hallucinations in technical pedagogy. Enforcing authority weighting at pre-retrieval and deterministic canonicalization eliminates authoritative drift while maintaining sub-millisecond execution latency.
