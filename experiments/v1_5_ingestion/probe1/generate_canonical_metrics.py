import json
import statistics
from datetime import datetime, timezone

# Load adjudication
with open('experiments/v1_5_ingestion/probe1/PROBE1_TEST_ADJUDICATION.jsonl') as f:
    adjudication = [json.loads(l) for l in f if l.strip()]

# Load baseline latencies
with open('experiments/v1_5_ingestion/probe1/PROBE1_TEST_BASELINE_RESULTS.jsonl') as f:
    baselines = [json.loads(l) for l in f if l.strip()]

# Confusion matrix
tp = sum(1 for a in adjudication if a['outcome_class'] == 'TP')
fp = sum(1 for a in adjudication if a['outcome_class'] == 'FP')
tn = sum(1 for a in adjudication if a['outcome_class'] == 'TN')
fn = sum(1 for a in adjudication if a['outcome_class'] == 'FN')

total_p = tp + fn
total_n = fp + tn
total_pages = len(adjudication)

mer = fn / total_p if total_p > 0 else None
fer = fp / total_n if total_n > 0 else None
acc = (tp + tn) / total_pages
prec = tp / (tp + fp) if (tp + fp) > 0 else None
rec = tp / total_p if total_p > 0 else None

# Structural quality
def compute_page_q(scores_dict, dims):
    return sum(scores_dict[d] for d in dims) / len(dims)

q_b0 = [compute_page_q(a['unblinded_scores']['pypdf'], a['applicable_dimensions']) for a in adjudication]
q_b1 = [compute_page_q(a['unblinded_scores']['pymupdf'], a['applicable_dimensions']) for a in adjudication]
q_b2 = [compute_page_q(a['unblinded_scores']['docling'], a['applicable_dimensions']) for a in adjudication]
q_b3 = [compute_page_q(a['unblinded_scores']['adaptive'], a['applicable_dimensions']) for a in adjudication]

mean_q_b0 = statistics.mean(q_b0)
mean_q_b1 = statistics.mean(q_b1)
mean_q_b2 = statistics.mean(q_b2)
mean_q_b3 = statistics.mean(q_b3)

# Latency statistics
def percentile(data, p):
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = int(k) + 1 if int(k) + 1 < len(sorted_data) else int(k)
    d = k - f
    return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])

lat_by_tool = {
    'pypdf': [b['latencies_ms']['pypdf'] for b in baselines],
    'pymupdf': [b['latencies_ms']['pymupdf'] for b in baselines],
    'docling': [b['latencies_ms']['docling'] for b in baselines],
    'adaptive': [b['latencies_ms']['adaptive'] for b in baselines]
}

telemetry_stats = {}
for tool, lats in lat_by_tool.items():
    telemetry_stats[tool] = {
        'total_ms': round(sum(lats), 2),
        'mean_ms': round(statistics.mean(lats), 2),
        'median_ms': round(statistics.median(lats), 2),
        'p95_ms': round(percentile(lats, 95), 2),
        'min_ms': round(min(lats), 2),
        'max_ms': round(max(lats), 2)
    }

rel_cost = telemetry_stats['adaptive']['total_ms'] / telemetry_stats['docling']['total_ms']

pareto_q = mean_q_b3 >= (mean_q_b2 - 0.15)
pareto_cost = rel_cost <= 0.50
pareto_efficient = pareto_q and pareto_cost

# Exit Gate check
# Pass: MER <= 0.10 and Q(B3) >= Q(B2) - 0.15 and rel_cost <= 0.50
# Partial: MER in (0.10, 0.20] or rel_cost > 0.50
# Fail: MER > 0.20 or Q(B3) < Q(B1)
if mer is not None and mer > 0.20:
    exit_gate = 'FAIL'
elif mer is not None and (mer > 0.10 or rel_cost > 0.50):
    exit_gate = 'PARTIAL'
elif pareto_efficient and (mer is not None and mer <= 0.10):
    exit_gate = 'PASS'
else:
    exit_gate = 'FAIL'

metrics_payload = {
    '$schema': 'https://raw.githubusercontent.com/guarnieriagustincyber/TALOS/main/schemas/probe1_test_metrics.schema.json',
    'experiment_id': 'exp_ingestion_probe0_v2',
    'phase': 'V1.5 — Phase 1 / Ingestion Intelligence Lab',
    'probe': 'PROBE-1: Adaptive Structural Routing',
    'split': 'TEST',
    'evaluation_timestamp': datetime.now(timezone.utc).isoformat(),
    'calibrated_router_version': 'v1.0.1-calibrated-frozen',
    'calibrated_router_hash': '8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe',
    'test_pages_count': total_pages,
    'confusion_matrix': {
        'TP': tp,
        'FP': fp,
        'TN': tn,
        'FN': fn,
        'total_positive': total_p,
        'total_negative': total_n,
        'total_pages': total_pages
    },
    'classification_metrics': {
        'missed_escalation_rate': round(mer, 4) if mer is not None else None,
        'missed_escalation_rate_pct': round(mer * 100, 2) if mer is not None else None,
        'false_escalation_rate': round(fer, 4) if fer is not None else None,
        'false_escalation_rate_pct': round(fer * 100, 2) if fer is not None else None,
        'accuracy': round(acc, 4),
        'accuracy_pct': round(acc * 100, 2),
        'precision': round(prec, 4) if prec is not None else None,
        'precision_pct': round(prec * 100, 2) if prec is not None else None,
        'recall': round(rec, 4) if rec is not None else None,
        'recall_pct': round(rec * 100, 2) if rec is not None else None
    },
    'structural_quality': {
        'mean_q_b0_pypdf': round(mean_q_b0, 4),
        'mean_q_b1_pymupdf': round(mean_q_b1, 4),
        'mean_q_b2_docling': round(mean_q_b2, 4),
        'mean_q_b3_adaptive': round(mean_q_b3, 4),
        'delta_b3_vs_b2': round(mean_q_b3 - mean_q_b2, 4),
        'delta_b3_vs_b1': round(mean_q_b3 - mean_q_b1, 4)
    },
    'computational_cost_and_latency': {
        'telemetry_by_baseline': telemetry_stats,
        'relative_cost_b3_vs_b2': round(rel_cost, 4),
        'cost_reduction_b3_vs_b2_pct': round((1.0 - rel_cost) * 100, 2)
    },
    'pareto_frontier_analysis': {
        'pareto_quality_threshold_q_b2_minus_0_15': round(mean_q_b2 - 0.15, 4),
        'q_b3_achieved': round(mean_q_b3, 4),
        'pareto_quality_condition_satisfied': pareto_q,
        'cost_ratio_threshold': 0.50,
        'cost_ratio_achieved': round(rel_cost, 4),
        'pareto_cost_condition_satisfied': pareto_cost,
        'pareto_efficient': pareto_efficient
    },
    'exit_gate_verdict': {
        'verdict': exit_gate,
        'safety_criterion_met': False,
        'safety_threshold_mer': '<= 10.0%',
        'safety_mer_achieved': f'{round(mer * 100, 2)}%',
        'verdict_rationale': (
            f"The adaptive router achieves Pareto efficiency on computational cost ({round(rel_cost*100, 2)}% vs <= 50.0%) "
            f"and preserves near-Docling mean quality (Q={round(mean_q_b3, 4)} vs target {round(mean_q_b2 - 0.15, 4)}). "
            f"However, it fails the critical safety exit gate because the Missed Escalation Rate is {round(mer*100, 2)}% (> 10.0% tolerance, and > 20.0% fail limit). "
            f"Four structurally complex pages (p078 borderless table, p085 concept diagram, p092 UML class diagram, p110 N-S diagram) "
            f"were not escalated due to low vector line counts and zero table grid lines. The router is rejected for production use in its current form."
        )
    }
}

with open('experiments/v1_5_ingestion/probe1/PROBE1_TEST_METRICS.json', 'w') as f:
    json.dump(metrics_payload, f, indent=2, ensure_ascii=False)

print("Generated PROBE1_TEST_METRICS.json successfully.")
print(json.dumps(metrics_payload['exit_gate_verdict'], indent=2))

