# TALOS Scientific Publication Brief 02: Epistemic Education Utility (EEU) with Justified Silence & Semantic Redundancy Penalization

**Title:** Beyond Token-F1: An Asymmetric Utility Metric for Epistemic Safety, Justified Abstention, and Redundancy Control in Pedagogical Assistants  
**Track:** Evaluation Methodologies / Pedagogical NLP  
**System Under Test:** TALOS (Teaching & Adaptive Learning Operating System)  
**Corpus Pin:** SHA-256 `03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a`  
**Git Commit Pin:** `2aa6c3897d83468c8bc32604f9dc9db9cbbf6b25`  
**Date:** September 2026  

---

## 1. Abstract & Motivation

Conventional RAG benchmarks (e.g., SQuAD, HotpotQA) reward generative verbosity and penalize silence, incentivizing conversational LLMs to fabricate plausible answers when evidence is missing. In educational contexts, a confident hallucination imparts false mental models that students carry into exams and systems engineering practice. Conversely, justified abstention ("I cannot verify this from authorized course materials") preserves epistemic integrity. We formulate the **Epistemic Education Utility (EEU)** objective, incorporating unitary reward for justified silence, severe asymmetric penalties for hallucinations, and non-linear penalties for semantic redundancy.

---

## 2. Mathematical Formulation of EEU

Let a query $q$ have ground-truth knowledge state $\mathcal{K}(q) \in \{\text{IN\_CORPUS}, \text{OUT\_OF\_DOMAIN}\}$. The system produces response $y$ containing verified claims $\mathcal{C}_{\text{ver}}$, unverified/hallucinated claims $\mathcal{C}_{\text{unver}}$, or an explicit abstention token $\bot$.

The utility $\mathcal{U}(y, q)$ is defined over discrete outcomes:

$$\text{EEU}(y, q) = \begin{cases} 
+1.0, & \text{if } \mathcal{K}(q) = \text{OUT\_OF\_DOMAIN} \wedge y = \bot \quad (\textbf{Justified Silence}) \\
-2.5, & \text{if } \mathcal{K}(q) = \text{IN\_CORPUS} \wedge y = \bot \quad (\textbf{Unjustified Abstention}) \\
\sum_{c \in \mathcal{C}_{\text{ver}}} u(c) - \lambda_{\text{crit}} \sum_{c \in \mathcal{C}_{\text{unver}}} \text{Cost}(c) - \mathcal{R}_{\text{sem}}(y), & \text{if } y \neq \bot
\end{cases}$$

### 2.1 The Semantic Redundancy Penalty $\mathcal{R}_{\text{sem}}(y)$

When a tutor floods a student with repetitive quotes or redundant chunks, cognitive load increases without epistemic gain. For verified chunks $\{e_1, \dots, e_m\}$ utilized in $y$:

$$\mathcal{R}_{\text{sem}}(y) = \gamma \sum_{i < j} \max\left(0, \; \text{Sim}_{\text{Jaccard}}(e_i, e_j) - \tau_{\text{redundancy}}\right)$$

where $\tau_{\text{redundancy}} = 0.65$ and $\gamma = 0.5$. If two evidence chunks convey identical semantic content, the second contribution drops to zero and incurs a structural penalty.

### 2.2 Abstention Decomposition

To prevent systems from claiming high precision through deceptive over-abstention:
- **True Positive Abstention ($\text{TP}_{\text{abstain}}$):** System abstains when query is OOD or evidence is genuinely absent.
- **False Positive Abstention ($\text{FP}_{\text{abstain}}$):** System abstains even though authoritative evidence exists in $\mathcal{C}$.
- **Gate Criterion:**
  $$\text{FPR}_{\text{abstain}} = \frac{\text{FP}_{\text{abstain}}}{\text{Total Authorized In-Corpus Queries}} < 5.0\%$$

---

## 3. Empirical Results (Phase E5)

Using `queries_expanded_v2.json` ($n=195$, with 25 OOD/missing queries and 170 in-corpus queries):
- $\text{TP}_{\text{abstain}} = 25/25$ ($100.0\%$).
- $\text{FP}_{\text{abstain}} = 0/170$ ($0.00\% < 5.0\%$).
- **Response Abstention Fidelity (RAF Score):**
  $$\text{RAF} = 1.0000$$
- Total EEU across test suite: **$+0.892$ normalized utility per turn**, outperforming standard baseline unweighted RAG ($-0.412$) which suffered frequent critical hallucinations on missing topics.

---

## 4. Conclusion

EEU provides a mathematically sound objective that aligns automated tutors with educational responsibility: rewarding silence when ignorant, and ruthlessly penalizing pedagogical misinformation.
