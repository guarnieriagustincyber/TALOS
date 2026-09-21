#!/usr/bin/env bash
set -e
echo "================================================================"
echo "RUNNING FULL RED TEAM ADVERSARIAL AUDIT CAMPAIGN"
echo "================================================================"

./.venv/bin/python red_team/repro/attack_01_privilege_escalation.py
./.venv/bin/python red_team/repro/attack_02_concurrency_race.py
./.venv/bin/python red_team/repro/attack_02b_schrodinger_crash.py
./.venv/bin/python red_team/repro/attack_03_rag_poisoning_isolation.py
./.venv/bin/python red_team/repro/attack_04_resource_bombs.py
./.venv/bin/python red_team/repro/attack_05_architectural_drift.py

echo "================================================================"
echo "ALL ATTACK SCRIPTS COMPLETED."
echo "================================================================"
