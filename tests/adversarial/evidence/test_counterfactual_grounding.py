"""Adversarial and Counterfactual Verification Test Suite (Phase E2.7).

Validates the robustness of TokenGroundingEngine and DeterministicAuditEngine
against 13 adversarial, counterfactual, and deceptive student/model prompts:
1. Zero NVMe latency paging (hardware physical limit)
2. Hardware interrupt disablement (kernel bypass illusion)
3. Degenerate BST O(n) claimed as O(log n)
4. Mode bit corruption in user space
5. Lossless TCP sequence numbering without packet drops
6. Cafeteria tray stack analogy (pedagogical valid vs overextended)
7. Post office box RAM analogy (pedagogical valid vs invalid literal)
8. Mergesort space complexity O(1) fallacy
9. QuickSort worst-case O(n log n) fallacy
10. Dijkstra with negative weights correctness fallacy
11. Two-phase locking deadlock prevention fallacy
12. Virtual memory zero internal fragmentation fallacy
13. Atomic CAS ABA problem immunity fallacy
"""

import pytest
from pathlib import Path
from study_engine.evidence.verification_backstop import GenerationVerificationBackstop
from study_engine.evidence.claim_extractor import DeterministicClaimExtractor, ClaimType, ClaimCriticality
from study_engine.evidence.token_grounding import TokenGroundingEngine, GroundingStatus


@pytest.fixture
def audit_engine():
    return GenerationVerificationBackstop()


@pytest.fixture
def grounder():
    dict_path = Path("data/benchmark/bilingual_dict_v1.json")
    return TokenGroundingEngine(bilingual_dict_path=dict_path)


# ==============================================================================
# 1. Zero NVMe Latency Paging
# ==============================================================================
def test_adv_01_zero_nvme_latency(audit_engine):
    evidence = [{
        "id": "EV-01",
        "content": "NVMe SSD paging introduces microsecond latencies (typically 10-50 microseconds), which is orders of magnitude slower than DRAM nanosecond access. Paging always incurs measurable latency."
    }]
    adversarial_response = "With modern NVMe disks, page faults execute in zero latency without any delay."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 2. Hardware Interrupt Disablement (Kernel Bypass Illusion)
# ==============================================================================
def test_adv_02_interrupt_disablement_user_mode(audit_engine):
    evidence = [{
        "id": "EV-02",
        "content": "Executing privileged instructions such as CLI to disable hardware interrupts in user mode causes a general protection fault (#GP); only the kernel in supervisor mode can manipulate interrupt flags."
    }]
    adversarial_response = "A user-space process can directly disable all hardware CPU interrupts using CLI without kernel privilege."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 3. Degenerate BST O(n) claimed as O(log n)
# ==============================================================================
def test_adv_03_degenerate_bst_complexity(audit_engine):
    evidence = [{
        "id": "EV-03",
        "content": "In an unbalanced or degenerate binary search tree, search degrades to O(n) worst-case time complexity, equivalent to a linked list, rather than logarithmic time."
    }]
    adversarial_response = "Even when completely degenerate, a binary search tree retains O(log n) worst-case search complexity."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 4. Mode Bit Corruption in User Space
# ==============================================================================
def test_adv_04_mode_bit_corruption(audit_engine):
    evidence = [{
        "id": "EV-04",
        "content": "The CPU hardware mode bit cannot be altered by user-space software instructions directly. Transition to kernel mode occurs strictly through hardware traps, system calls, or interrupts."
    }]
    adversarial_response = "An unprivileged application can alter the CPU hardware mode bit through simple pointer arithmetic to gain kernel mode privileges."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 5. Lossless TCP Sequence Numbering Fallacy
# ==============================================================================
def test_adv_05_tcp_lossless_physical_illusion(audit_engine):
    evidence = [{
        "id": "EV-05",
        "content": "TCP sequence numbers and acknowledgments provide reliable logical delivery by detecting lost packets and retransmitting them, but physical network interfaces can still drop packets."
    }]
    adversarial_response = "TCP sequence numbering guarantees that packets are never dropped at the physical network layer."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 6. Cafeteria Tray Stack Analogy (Pedagogical Valid vs Overextended)
# ==============================================================================
def test_adv_06_cafeteria_tray_stack(audit_engine):
    evidence = [{
        "id": "EV-06",
        "content": "A call stack operates on a LIFO (Last-In First-Out) discipline. Operations are restricted to push and pop at the top of the stack; elements below the top cannot be directly accessed in O(1)."
    }]
    # Case 6a: Valid pedagogical framing passes
    valid_pedagogical = (
        "In operating systems, the call stack follows a last-in first-out discipline. "
        "Como analogía didáctica, una pila funciona como una bandeja de cafetería donde solo se accede al tope."
    )
    res_valid = audit_engine.verify_e2_claims(valid_pedagogical, evidence)
    assert res_valid["verdict"] == "APPROVED"

    # Case 6b: Deceptive overextension claiming arbitrary random access in O(1) fails
    invalid_pedagogical = (
        "In operating systems, the call stack allows random index access to all middle elements in O(1) [EV-06]."
    )
    res_invalid = audit_engine.verify_e2_claims(invalid_pedagogical, evidence)
    assert res_invalid["verdict"] == "REJECTED_UNSUPPORTED"


# ==============================================================================
# 7. Post Office Box RAM Analogy (Pedagogical Valid vs Literal Absurdity)
# ==============================================================================
def test_adv_07_post_office_box_ram(audit_engine):
    evidence = [{
        "id": "EV-07",
        "content": "Random Access Memory assigns a distinct numerical address to each memory cell, allowing uniform access times regardless of location."
    }]
    # Case 7a: Valid pedagogical analogy
    valid_analogy = (
        "Random Access Memory assigns a distinct numerical address to each memory cell [EV-07]. "
        "Como analogía didáctica, podemos imaginar la memoria como casilleros postales numerados."
    )
    res_valid = audit_engine.verify_e2_claims(valid_analogy, evidence)
    assert res_valid["verdict"] == "APPROVED"

    # Case 7b: Literal absurdity claiming physical mail and wood
    invalid_claim = (
        "Random Access Memory contains wooden pigeonhole slots that physically store paper letters."
    )
    res_invalid = audit_engine.verify_e2_claims(invalid_claim, evidence)
    assert res_invalid["verdict"] == "REJECTED_UNSUPPORTED"


# ==============================================================================
# 8. Mergesort Space Complexity O(1) Fallacy
# ==============================================================================
def test_adv_08_mergesort_space_complexity(audit_engine):
    evidence = [{
        "id": "EV-08",
        "content": "Standard array-based mergesort requires O(n) auxiliary space to merge sorted subarrays. It does not run in O(1) auxiliary space."
    }]
    adversarial_response = "Standard array-based mergesort achieves an auxiliary space complexity of O(1) during the merge step."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 9. QuickSort Worst-Case O(n log n) Fallacy
# ==============================================================================
def test_adv_09_quicksort_worst_case(audit_engine):
    evidence = [{
        "id": "EV-09",
        "content": "QuickSort exhibits an average-case time complexity of O(n log n), but its worst-case time complexity degrades to O(n^2) when poor pivots are chosen."
    }]
    adversarial_response = "Quicksort has a worst-case time complexity of O(n log n) even with unbalanced partitions."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 10. Dijkstra with Negative Weights Fallacy
# ==============================================================================
def test_adv_10_dijkstra_negative_weights(audit_engine):
    evidence = [{
        "id": "EV-10",
        "content": "Dijkstra's algorithm assumes non-negative edge weights; it produces incorrect shortest path distances in graphs with negative weight edges or cycles. Bellman-Ford must be used instead."
    }]
    adversarial_response = "Dijkstra algorithm correctly computes shortest paths in graphs with negative weight edges and negative cycles."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 11. Two-Phase Locking Deadlock Prevention Fallacy
# ==============================================================================
def test_adv_11_two_phase_locking_deadlocks(audit_engine):
    evidence = [{
        "id": "EV-11",
        "content": "Two-phase locking (2PL) guarantees conflict serializability of database schedules, but it does not prevent deadlocks; transactions may still enter circular waits requiring detection or timeouts."
    }]
    adversarial_response = "Strict two-phase locking completely prevents deadlocks from occurring in database transactions."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 12. Virtual Memory Zero Internal Fragmentation Fallacy
# ==============================================================================
def test_adv_12_virtual_memory_internal_fragmentation(audit_engine):
    evidence = [{
        "id": "EV-12",
        "content": "Paging eliminates external fragmentation by using fixed-size page frames, but internal fragmentation persists on the last page allocated to a process."
    }]
    adversarial_response = "Paging in virtual memory removes any internal fragmentation and guarantees zero wasted memory inside page frames."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"


# ==============================================================================
# 13. Atomic CAS ABA Problem Fallacy
# ==============================================================================
def test_adv_13_atomic_cas_aba_problem(audit_engine):
    evidence = [{
        "id": "EV-13",
        "content": "Atomic Compare-And-Swap (CAS) instructions check if a memory location equals an expected value, but standard CAS is susceptible to the ABA problem unless combined with tagged pointers or version counters."
    }]
    adversarial_response = "Compare-and-swap CAS operations inherently eliminate the ABA problem without requiring version tags or counters."
    result = audit_engine.verify_e2_claims(adversarial_response, evidence)
    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["action"] == "HARD_ABSTENTION"
