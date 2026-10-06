import hashlib
import json
import os
from datetime import datetime, timezone

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

files_to_seal = [
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_MANIFEST.json',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_IMPLEMENTATION_PREFLIGHT.md',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_FEATURES.jsonl',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_ROUTER_RESULTS.jsonl',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_BASELINE_RESULTS.jsonl',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_ADJUDICATION.jsonl',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_METRICS.json',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_EXECUTION_AUDIT.md',
    'experiments/v1_5_ingestion/probe1/PROBE1_TEST_FINAL_REPORT.md',
    'drive_upload_ingestion_probe1_test/data/joyanes_ch02_test_19p.pdf',
    'drive_upload_ingestion_probe1_test/PROBE1_TEST_RESULTS.zip'
]

sealed_files = {}
for relpath in files_to_seal:
    if os.path.exists(relpath):
        fhash = sha256_file(relpath)
        fsize = os.path.getsize(relpath)
        sealed_files[relpath] = {
            'sha256': fhash,
            'size_bytes': fsize
        }
        print(f"Hashed {relpath}: {fhash}")
    else:
        print(f"WARNING: File not found: {relpath}")

# Calculate overall manifest digest
concatenated = "".join(f"{k}:{v['sha256']}" for k, v in sorted(sealed_files.items()))
overall_digest = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()

manifest = {
    '$schema': 'https://raw.githubusercontent.com/guarnieriagustincyber/TALOS/main/schemas/probe1_test_seal_manifest.schema.json',
    'seal_id': 'probe1_test_execution_seal_v1',
    'sealed_at': datetime.now(timezone.utc).isoformat(),
    'probe_id': 'PROBE-1: Adaptive Structural Routing',
    'phase': 'TEST Execution and Blind Evaluation',
    'overall_test_seal_digest_sha256': overall_digest,
    'governance': {
        'status': 'SEALED_TEST_COMPLETED',
        'calibrated_router_version': 'v1.0.1-calibrated-frozen',
        'calibrated_router_hash': '8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe',
        'exit_gate_verdict': 'FAIL',
        'production_promotion_permitted': False,
        'zero_recalibration_verified': True,
        'database_changes': 0
    },
    'sealed_artifacts': sealed_files
}

out_path = 'experiments/v1_5_ingestion/probe1/PROBE1_TEST_SEAL_MANIFEST.json'
with open(out_path, 'w') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with overall digest: {overall_digest}")
