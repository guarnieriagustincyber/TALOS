import { useState, useCallback } from 'react';
import { SandboxFsmState, PracticeEvaluateResponse } from '@domain/types';

interface BackendPracticeResponse {
  task_id: string;
  status: 'PASSED' | 'FAILED' | 'ABSTAINED';
  assertions: Array<{
    id: string;
    description: string;
    passed: boolean;
    error_detail?: string | null;
  }>;
  assertions_passed: number;
  assertions_total: number;
  execution_time_ms: number;
  stdout: string;
  stderr: string;
  ledger_block_hash?: string | null;
  ledger_timestamp?: string | null;
}

export function useSandboxFsm(taskId: string = 'task_net_tcp_01') {
  const [fsmState, setFsmState] = useState<SandboxFsmState>('IDLE');
  const [assessment, setAssessment] = useState<PracticeEvaluateResponse | null>(null);

  const requestEvaluation = useCallback(async () => {
    if (fsmState !== 'IDLE' && fsmState !== 'READY') return;

    setFsmState('EVALUATION_REQUESTED');

    try {
      setFsmState('SANDBOX_RUNNING');

      const response = await fetch('/api/practice/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          file_path: "labs/net_tcp_syn.py",
          command: ":eval",
        }),
      });

      if (!response.ok) {
        setFsmState('FAILED');
        return;
      }

      const data: BackendPracticeResponse = await response.json();

      const adapted: PracticeEvaluateResponse = {
        exercise_id: data.task_id,
        fsm_state: data.status as SandboxFsmState,
        passed_assertions: data.assertions_passed,
        total_assertions: data.assertions_total,
        assertions: data.assertions.map((a) => ({
          id: a.id,
          description: a.description,
          passed: a.passed,
          error_message: a.error_detail || undefined,
        })),
        ledger_block_hash: data.ledger_block_hash,
        timestamp_utc: data.ledger_timestamp || new Date().toISOString(),
      };

      setAssessment(adapted);
      setFsmState('ASSESSMENT_RECEIVED');

      // Regla ADR-008 Sección 6: PASSED solo con ledger_block_hash válido y N/N aserciones
      const isAllPassed = adapted.passed_assertions === adapted.total_assertions;
      const hasLedgerBlock = Boolean(adapted.ledger_block_hash);

      if (isAllPassed && hasLedgerBlock) {
        setFsmState('PASSED');
      } else if (!isAllPassed) {
        setFsmState('FAILED');
      } else {
        setFsmState('ABSTAINED');
      }
    } catch {
      setFsmState('FAILED');
    }
  }, [taskId, fsmState]);

  const resetFsm = useCallback(() => {
    setFsmState('IDLE');
    setAssessment(null);
  }, []);

  return {
    fsmState,
    assessment,
    requestEvaluation,
    resetFsm,
  };
}
