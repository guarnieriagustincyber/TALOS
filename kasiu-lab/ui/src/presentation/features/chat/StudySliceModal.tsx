import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  AlertTriangle,
  Sparkles,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Terminal,
  Cpu,
  Database,
  Network
} from 'lucide-react';
import type { StudySessionSnapshotData } from './OpeningBriefView';
import { studySessionService } from '../../../services/studySessionService';
import { createExerciseAttemptId } from '../../../services/chatService';
import type { EpisodeAttemptRecord } from '../../../services/episodeAttemptService';
import {
  readEpisodeAttemptRecord,
  writeEpisodeAttemptRecord,
} from '../../../services/episodeAttemptService';

interface KCItem {
  kc_id: string;
  title: string;
  unit: number;
  priority: string;
  contextual_status: string;
  bkt: {
    p_L: number;
    attempts: number;
  };
}

interface ConceptPacketData {
  kc_id: string;
  notebook_id: string;
  objective: string;
  core_concept: string;
  mental_model: string;
  reasoning_guidance: string;
  formalization?: string;
  implementation_guidance?: string;
  pitfalls: string[];
  audit_verdict: string;
}

interface ExerciseData {
  exercise_id: string;
  kc_id: string;
  prompt: string;
  exercise_type: 'MC' | 'EXACT_TEXT' | 'NUMERIC';
  options?: string[];
  verification_status: string;
}

interface NotebookKCsResponse {
  notebook_id: string;
  name: string;
  kcs: KCItem[];
  consultive_student_context: {
    current_position: string;
    errors_recurring: string[];
    topics_seen: string[];
  };
}

interface CurricularFolder {
  id: string;
  name: string;
  subfolders?: CurricularFolder[];
  notebooks?: {
    id: string;
    name: string;
    icon: 'terminal' | 'cpu' | 'database' | 'network';
    path: string;
  }[];
}

const CURRICULUM_TREE: CurricularFolder[] = [
  {
    id: 'fadena',
    name: 'fadena',
    subfolders: [
      {
        id: 'fadena_1ano',
        name: '1erAño',
        subfolders: [
          {
            id: 'fadena_1ano_2cuat',
            name: '2doCuatrimestre',
            notebooks: [
              {
                id: 'fadena-lenguajes',
                name: 'Lenguajes de Programación',
                icon: 'terminal',
                path: 'fadena / 1erAño / 2doCuatrimestre / Lenguajes de Programación',
              },
              {
                id: 'fadena-so2',
                name: 'Sistemas Operativos II',
                icon: 'cpu',
                path: 'fadena / 1erAño / 2doCuatrimestre / Sistemas Operativos II',
              },
              {
                id: 'fadena-std',
                name: 'Sistema de Tratamiento de Datos',
                icon: 'database',
                path: 'fadena / 1erAño / 2doCuatrimestre / Sistema de Tratamiento de Datos',
              },
              {
                id: 'fadena-teleco',
                name: 'Infraestructura de Telecomunicaciones',
                icon: 'network',
                path: 'fadena / 1erAño / 2doCuatrimestre / Telecomunicaciones',
              },
            ],
          },
        ],
      },
    ],
  },
  {
    id: 'roadmap',
    name: 'Roadmap',
    subfolders: [
      {
        id: 'roadmap_fase0',
        name: 'Fase0',
        notebooks: [
          {
            id: 'fase0-soc',
            name: 'Programación y Pensamiento Algorítmico',
            icon: 'terminal',
            path: 'Roadmap / Fase0 / Programación',
          },
        ],
      },
    ],
  },
];

const isSelectableNotebook = (notebookId?: string): notebookId is string => {
  if (!notebookId) return false;
  const syntheticId = typeof window !== 'undefined' ? window.__TALOS_DEFAULT_NOTEBOOK_ID__ : undefined;
  if (typeof window !== 'undefined' && window.__TALOS_SYNTHETIC_PROFILE__) {
    return Boolean(syntheticId && notebookId === syntheticId);
  }
  return [
    'fase0-soc', 'fadena-lenguajes', 'fadena-so2', 'fadena-std', 'fadena-teleco',
    ...(syntheticId ? [syntheticId] : []),
  ].includes(notebookId);
};

const renderNbIcon = (icon: string) => {
  switch (icon) {
    case 'cpu':
      return <Cpu className="h-3.5 w-3.5 text-purple-400 shrink-0" />;
    case 'database':
      return <Database className="h-3.5 w-3.5 text-amber-400 shrink-0" />;
    case 'network':
      return <Network className="h-3.5 w-3.5 text-rose-400 shrink-0" />;
    default:
      return <Terminal className="h-3.5 w-3.5 text-cyan-400 shrink-0" />;
  }
};

export const StudySliceModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  initialNotebookId?: string;
  onSessionUpdate?: (snapshot: StudySessionSnapshotData) => void;
}> = ({
  isOpen,
  onClose,
  initialNotebookId,
  onSessionUpdate,
}) => {
  const [selectedNotebook, setSelectedNotebookState] = useState<string>(() =>
    isSelectableNotebook(initialNotebookId) ? initialNotebookId : 'fase0-soc'
  );
  const manualNotebookSelectionRef = React.useRef(false);
  const wasOpenRef = React.useRef(false);
  const lastInitialNotebookRef = React.useRef(initialNotebookId);
  const selectNotebook = (notebookId: string) => {
    if (!isSelectableNotebook(notebookId)) {
      setFlowError('Este perfil de validación solo permite cuadernos sintéticos autorizados.');
      return;
    }
    manualNotebookSelectionRef.current = true;
    setSelectedNotebookState(notebookId);
  };
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(['fadena', 'fadena_1ano', 'fadena_1ano_2cuat', 'roadmap', 'roadmap_fase0'])
  );
  const [catalog, setCatalog] = useState<NotebookKCsResponse | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [activeEpisodeId, setActiveEpisodeId] = useState<string | null>(null);
  const [concept, setConcept] = useState<ConceptPacketData | null>(null);
  const [exercise, setExercise] = useState<ExerciseData | null>(null);
  const [stepId, setStepId] = useState<string | null>(null);
  const [userResponse, setUserResponse] = useState('');
  const [gradingResult, setGradingResult] = useState<any | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [studySessionSnapshot, setStudySessionSnapshot] = useState<StudySessionSnapshotData | null>(null);
  const [sessionStatus, setSessionStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [flowError, setFlowError] = useState<string | null>(null);
  const [submissionState, setSubmissionState] = useState<'idle' | 'submitting' | 'unknown' | 'incomplete' | 'conflict' | 'graded' | 'ungraded'>('idle');
  const [submittedResponse, setSubmittedResponse] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [attemptHistory, setAttemptHistory] = useState<EpisodeAttemptRecord['history']>([]);
  const [attemptPersistenceBlocked, setAttemptPersistenceBlocked] = useState(false);
  const submissionLockRef = React.useRef(false);

  const persistEpisodeAttempt = (
    sessionId: string,
    episodeId: string,
    exerciseId: string,
    current: EpisodeAttemptRecord['current'],
    history: EpisodeAttemptRecord['history'],
  ): boolean => {
    try {
      const record: EpisodeAttemptRecord = {
        version: 1, sessionId, episodeId, exerciseId, current, history,
      };
      writeEpisodeAttemptRecord(window.localStorage, record);
      setAttemptPersistenceBlocked(false);
      return true;
    } catch {
      setAttemptPersistenceBlocked(true);
      setFlowError('No se pudo conservar la identidad del intento; la respuesta no fue enviada.');
      return false;
    }
  };

  const restoreEpisodeAttempt = (sessionId: string, episodeId: string, exerciseId: string) => {
    try {
      const record = readEpisodeAttemptRecord(window.localStorage, sessionId, episodeId, exerciseId);
      if (!record) {
        setAttemptId(null);
        setAttemptHistory([]);
        setSubmittedResponse(null);
        setUserResponse('');
        setGradingResult(null);
        setSubmissionState('idle');
        setAttemptPersistenceBlocked(false);
        return;
      }
      const current = record.current;
      setAttemptId(current?.attemptId || null);
      setAttemptHistory(record.history);
      setSubmittedResponse(current?.answer || null);
      setUserResponse(current?.answer || '');
      setSubmissionState(current?.status || 'idle');
      setGradingResult(current?.status === 'graded' ? current.result || null : null);
      const storedMessage = typeof current?.message === 'string'
        ? current.message
        : typeof current?.result?.detail === 'string'
          ? current.result.detail
          : typeof current?.result?.feedback === 'string'
            ? current.result.feedback
            : 'El intento restaurado necesita reconciliación.';
      setFlowError(current && current.status !== 'graded'
        ? storedMessage
        : null);
      setAttemptPersistenceBlocked(false);
    } catch (error) {
      setAttemptId(null);
      setSubmittedResponse(null);
      setGradingResult(null);
      setAttemptHistory([]);
      setAttemptPersistenceBlocked(true);
      setSubmissionState('conflict');
      setFlowError(error instanceof Error ? error.message : 'No se pudo verificar la identidad del intento guardado.');
    }
  };

  const restoreEpisodeExercise = async (episodeId: string, sessionId: string) => {
    const response = await fetch(`/api/pedagogy/episode/${episodeId}/next`);
    if (!response.ok) throw new Error(`No se pudo recuperar el ejercicio (HTTP ${response.status}).`);
    const payload = await response.json();
    if (
      payload.intervention_type !== 'EXERCISE' ||
      payload.episode_id !== episodeId ||
      payload.session_id !== sessionId ||
      payload.notebook_id !== selectedNotebook ||
      typeof payload.step_id !== 'string' ||
      payload.exercise?.exercise_id !== payload.step_id.replace(/^step_eval_/, '')
    ) {
      throw new Error('El ejercicio recuperado no coincide con las identidades persistidas de sesión y episodio.');
    }
    const refreshed = await studySessionService.getSnapshot(sessionId);
    if (
      refreshed.session_id !== sessionId ||
      refreshed.episode_id !== episodeId ||
      refreshed.notebook_id !== selectedNotebook ||
      refreshed.current_kc_id !== payload.exercise.kc_id ||
      refreshed.episode_phase !== 'EVALUATING'
    ) {
      throw new Error('El snapshot no confirma la identidad del episodio reanudado.');
    }
    restoreEpisodeAttempt(sessionId, episodeId, payload.exercise.exercise_id);
    setStudySessionSnapshot(refreshed);
    onSessionUpdate?.(refreshed);
    setStepId(payload.step_id);
    setExercise(payload.exercise);
  };

  // Sync initialNotebookId when modal opens
  useEffect(() => {
    if (!isOpen) {
      wasOpenRef.current = false;
      return;
    }
    if (
      isSelectableNotebook(initialNotebookId) &&
      (!wasOpenRef.current || lastInitialNotebookRef.current !== initialNotebookId)
    ) {
      wasOpenRef.current = true;
      lastInitialNotebookRef.current = initialNotebookId;
      manualNotebookSelectionRef.current = false;
      setSelectedNotebookState(initialNotebookId);
    }
  }, [isOpen, initialNotebookId]);

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  useEffect(() => {
    if (!isOpen) return;
    if (
      isSelectableNotebook(initialNotebookId) &&
      !manualNotebookSelectionRef.current &&
      selectedNotebook !== initialNotebookId
    ) return;
    const controller = new AbortController();
    setLoadingCatalog(true);
    setConcept(null);
    setExercise(null);
    setGradingResult(null);
    setUserResponse('');
    setActiveEpisodeId(null);
    setStepId(null);

    fetch(`/api/pedagogy/notebook/${selectedNotebook}/kcs`, { signal: controller.signal })
      .then((res) => res.json())
      .then((data) => {
        setCatalog(data);
        setLoadingCatalog(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Failed to load KCs:', err);
          setLoadingCatalog(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [isOpen, selectedNotebook, initialNotebookId]);

  useEffect(() => {
    if (!isOpen) return;
    if (
      isSelectableNotebook(initialNotebookId) &&
      !manualNotebookSelectionRef.current &&
      selectedNotebook !== initialNotebookId
    ) return;
    let active = true;
    setSessionStatus('loading');
    setStudySessionSnapshot(null);
    setFlowError(null);
    studySessionService.restoreOrOpenSession(selectedNotebook, studySessionService.getClientStudentId())
      .then(({ snapshot }) => {
        if (!active) return;
        setStudySessionSnapshot(snapshot);
        setSessionStatus('ready');
        onSessionUpdate?.(snapshot);
        if (snapshot.episode_id && snapshot.episode_phase === 'EVALUATING') {
          setActiveEpisodeId(snapshot.episode_id);
          void restoreEpisodeExercise(snapshot.episode_id, snapshot.session_id).catch((error) => {
            if (active) setFlowError(error instanceof Error ? error.message : 'No se pudo restaurar el ejercicio activo.');
          });
        } else if (snapshot.episode_id) {
          setActiveEpisodeId(snapshot.episode_id);
          setFlowError('Se restauró el episodio, pero su explicación no forma parte del snapshot. Podés reabrirla explícitamente para continuar.');
        }
      })
      .catch((error) => {
        if (!active) return;
        setSessionStatus('error');
        setFlowError(error instanceof Error ? error.message : 'No se pudo restaurar la sesión.');
      });
    return () => { active = false; };
  }, [isOpen, selectedNotebook, initialNotebookId, onSessionUpdate]);

  const handleStartStudy = async (kcId: string) => {
    setConcept(null);
    setExercise(null);
    setGradingResult(null);
    setUserResponse('');
    setSubmissionState('idle');
    setSubmittedResponse(null);
    setAttemptId(null);
    setAttemptHistory([]);
    setAttemptPersistenceBlocked(false);
    setFlowError(null);

    try {
      if (!studySessionSnapshot || studySessionSnapshot.notebook_id !== selectedNotebook) {
        throw new Error('No hay una sesión persistida del cuaderno seleccionado.');
      }
      let snapshot = studySessionSnapshot;
      if (snapshot.current_kc_id !== kcId) {
        if (!snapshot.available_actions.includes('SELECT_DIFFERENT_KC')) {
          throw new Error('La sesión restaurada no permite cambiar de KC en su fase actual.');
        }
        snapshot = await studySessionService.executeAction(snapshot.session_id, 'SELECT_DIFFERENT_KC', { kc_id: kcId });
      }
      if (!snapshot.episode_id) {
        if (!snapshot.available_actions.includes('START_EXPLANATION')) {
          throw new Error('La sesión no permite iniciar un episodio desde su estado actual.');
        }
        snapshot = await studySessionService.executeAction(snapshot.session_id, 'START_EXPLANATION');
      }
      const epId = snapshot.episode_id;
      if (!epId) throw new Error('El servidor no devolvió la identidad persistida del episodio.');
      setStudySessionSnapshot(snapshot);
      onSessionUpdate?.(snapshot);
      setActiveEpisodeId(epId);

      // 2. Fetch Concept
      const cRes = await fetch(`/api/pedagogy/episode/${epId}/concept`);
      if (!cRes.ok) throw new Error(`No se pudo recuperar el concepto (HTTP ${cRes.status}).`);
      const cData = await cRes.json();
      if (cData.status === 'PRESENTABLE' && cData.packet) {
        setConcept(cData.packet);
      } else if (cData.status === 'ABSTAINED') {
        // M1-02 (contrato SSE→UI sin éxito falso, aplicado al slice): la
        // abstención de S4.4 es un estado pedagógico legítimo y se presenta
        // como tal; jamás se silencia ni se sustituye por contenido no
        // aprobado.
        setFlowError(
          `TALOS se abstiene de presentar el concepto (S4.4: ${cData.audit_verdict ?? 'sin veredicto'}): ${cData.abstention_reason ?? 'sin detalle'}`
        );
      }

      // 3. Fetch Next Intervention (Exercise)
      const nextRes = await fetch(`/api/pedagogy/episode/${epId}/next`);
      if (!nextRes.ok) throw new Error(`No se pudo recuperar la intervención (HTTP ${nextRes.status}).`);
      const nextData = await nextRes.json();
      if (nextData.intervention_type === 'EXERCISE') {
        if (
          nextData.episode_id !== epId ||
          nextData.session_id !== snapshot.session_id ||
          nextData.notebook_id !== selectedNotebook ||
          nextData.exercise?.kc_id !== kcId ||
          typeof nextData.step_id !== 'string' ||
          nextData.step_id !== `step_eval_${nextData.exercise?.exercise_id}`
        ) {
          throw new Error('La intervención no coincide con la identidad persistida de sesión, episodio y KC.');
        }
        const refreshed = await studySessionService.getSnapshot(snapshot.session_id);
        if (
          refreshed.session_id !== snapshot.session_id ||
          refreshed.episode_id !== epId ||
          refreshed.notebook_id !== selectedNotebook ||
          refreshed.current_kc_id !== kcId ||
          refreshed.episode_phase !== 'EVALUATING'
        ) {
          throw new Error('El snapshot no confirma la identidad del ejercicio presentado.');
        }
        restoreEpisodeAttempt(refreshed.session_id, epId, nextData.exercise.exercise_id);
        setStudySessionSnapshot(refreshed);
        onSessionUpdate?.(refreshed);
        setStepId(nextData.step_id);
        setExercise(nextData.exercise);
      } else {
        setFlowError('El episodio no tiene una intervención de ejercicio disponible en este momento.');
      }
    } catch (err) {
      console.error('Error in study flow:', err);
      setFlowError(err instanceof Error ? err.message : 'No se pudo iniciar el ejercicio.');
    }
  };

  const submitEpisodeResponse = async (answer: string) => {
    if (
      !activeEpisodeId || !stepId || !exercise || stepId !== `step_eval_${exercise.exercise_id}` ||
      !answer.trim() || submissionLockRef.current ||
      attemptPersistenceBlocked ||
      !studySessionSnapshot?.session_id ||
      studySessionSnapshot.episode_id !== activeEpisodeId ||
      studySessionSnapshot.notebook_id !== selectedNotebook
    ) {
      if (!studySessionSnapshot?.session_id || studySessionSnapshot.episode_id !== activeEpisodeId) {
        setFlowError('No se puede evaluar: la sesión y el episodio activos no coinciden.');
      }
      return;
    }
    let stableAttemptId = attemptId;
    if (!stableAttemptId) {
      try {
        stableAttemptId = createExerciseAttemptId();
      } catch (error) {
        setAttemptPersistenceBlocked(true);
        setFlowError(error instanceof Error ? error.message : 'No se pudo crear la identidad del intento.');
        return;
      }
    }
    const attempt = {
      attemptId: stableAttemptId,
      answer,
      status: 'submitting' as const,
    };
    if (!persistEpisodeAttempt(
      studySessionSnapshot.session_id,
      activeEpisodeId,
      exercise.exercise_id,
      attempt,
      attemptHistory,
    )) return;

    setAttemptId(stableAttemptId);
    submissionLockRef.current = true;
    setIsSubmitting(true);
    setSubmissionState('submitting');
    setSubmittedResponse(answer);
    setFlowError(null);
    let refreshAfterResult = false;
    try {
      const res = await fetch(`/api/pedagogy/episode/${activeEpisodeId}/dialogue/evaluate-socratic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_response: answer,
          kc_id: exercise.kc_id,
          exercise_id: exercise.exercise_id,
          session_id: studySessionSnapshot.session_id,
          attempt_id: stableAttemptId,
          is_mc: exercise.exercise_type === 'MC',
          options_count: exercise.exercise_type === 'MC' ? exercise.options?.length ?? null : null,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = typeof data.detail === 'string' ? data.detail : `La evaluación fue rechazada (HTTP ${res.status}).`;
        const nextStatus = res.status >= 500
          ? 'unknown'
          : res.status === 409 && /incomplet/i.test(detail) ? 'incomplete' : 'conflict';
        setSubmissionState(nextStatus);
        setFlowError(detail);
        persistEpisodeAttempt(
          studySessionSnapshot.session_id,
          activeEpisodeId,
          exercise.exercise_id,
          { ...attempt, status: nextStatus },
          attemptHistory,
        );
        return;
      }
      if (data.status !== 'EVALUATED' && data.status !== 'UNGRADED') {
        throw new Error('El servidor devolvió un estado de evaluación no reconocido.');
      }
      if (data.status === 'EVALUATED' && typeof data.is_correct !== 'boolean') {
        throw new Error('La respuesta del servidor no incluye un veredicto verificable.');
      }
      refreshAfterResult = true;
      const nextStatus = data.status === 'EVALUATED' ? 'graded' : 'ungraded';
      setGradingResult(data.status === 'EVALUATED' ? data : null);
      setSubmissionState(nextStatus);
      persistEpisodeAttempt(
        studySessionSnapshot.session_id,
        activeEpisodeId,
        exercise.exercise_id,
        { ...attempt, status: nextStatus, result: data },
        attemptHistory,
      );
      if (data.status === 'UNGRADED') setFlowError(data.feedback || 'El servidor no pudo verificar el ejercicio.');
    } catch (err) {
      console.error('Error submitting response:', err);
      setSubmissionState('unknown');
      const detail = err instanceof Error
        ? err.message
        : 'No se conoce si el servidor completó esta operación.';
      setFlowError(`${detail} Reintentá solo el mismo texto y la misma identidad.`);
      persistEpisodeAttempt(
        studySessionSnapshot.session_id,
        activeEpisodeId,
        exercise.exercise_id,
        { ...attempt, status: 'unknown', message: detail },
        attemptHistory,
      );
    } finally {
      setIsSubmitting(false);
      submissionLockRef.current = false;
    }

    if (refreshAfterResult) {
      try {
        const refreshed = await studySessionService.getSnapshot(studySessionSnapshot.session_id);
        setStudySessionSnapshot(refreshed);
        onSessionUpdate?.(refreshed);
      } catch (error) {
        console.warn('No se pudo refrescar el snapshot después de evaluar:', error);
      }
      fetch(`/api/pedagogy/notebook/${selectedNotebook}/kcs`)
        .then((response) => response.json())
        .then((data) => setCatalog(data))
        .catch((error) => console.error('Error refreshing KCs catalog:', error));
    }
  };

  const handleSendResponse = () => {
    if (submissionState !== 'idle') return;
    void submitEpisodeResponse(userResponse.trim());
  };

  const handleRetrySameAttempt = () => {
    if (submissionState !== 'unknown' || !submittedResponse || !attemptId) return;
    void submitEpisodeResponse(submittedResponse);
  };

  const handleNewAttempt = () => {
    if (submissionState !== 'graded' || !attemptId || !exercise || !activeEpisodeId || !studySessionSnapshot) return;
    const completed = {
      attemptId,
      answer: submittedResponse || userResponse,
      status: 'graded' as const,
      result: gradingResult,
    };
    const nextHistory = [...attemptHistory, completed];
    if (!persistEpisodeAttempt(
      studySessionSnapshot.session_id,
      activeEpisodeId,
      exercise.exercise_id,
      null,
      nextHistory,
    )) return;
    setAttemptHistory(nextHistory);
    setAttemptId(null);
    setSubmittedResponse(null);
    setUserResponse('');
    setGradingResult(null);
    setSubmissionState('idle');
    setFlowError(null);
  };

  const handleExplicitResume = async () => {
    const episodeId = studySessionSnapshot?.episode_id;
    if (!episodeId || !studySessionSnapshot.session_id) return;
    setFlowError(null);
    try {
      const response = await fetch(`/api/pedagogy/episode/${episodeId}/concept`);
      if (!response.ok) throw new Error(`No se pudo reabrir la explicación (HTTP ${response.status}).`);
      const payload = await response.json();
      if (payload.status === 'PRESENTABLE' && payload.packet) setConcept(payload.packet);
      else throw new Error(payload.abstention_reason || 'La explicación no está disponible para este episodio.');
      await restoreEpisodeExercise(episodeId, studySessionSnapshot.session_id);
    } catch (error) {
      setFlowError(error instanceof Error ? error.message : 'No se pudo reabrir el episodio.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 text-white">
      <div className="flex h-[90vh] w-[95vw] max-w-6xl flex-col rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-3.5">
          <div className="flex items-center space-x-3">
            <BookOpen className="h-5 w-5 text-emerald-400" />
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-slate-100">TALOS — Modo de Estudio Curricular</h2>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
                  ARQUITECTURA CURRICULAR
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {selectedNotebook === 'fase0-soc' && 'Roadmap / Fase0 / Programación y Pensamiento Algorítmico'}
                {selectedNotebook === 'fadena-lenguajes' && 'fadena / 1erAño / 2doCuatrimestre / Lenguajes de Programación'}
                {selectedNotebook === 'fadena-so2' && 'fadena / 1erAño / 2doCuatrimestre / Sistemas Operativos II'}
                {selectedNotebook === 'fadena-std' && 'fadena / 1erAño / 2doCuatrimestre / Sistema de Tratamiento de Datos'}
                {selectedNotebook === 'fadena-teleco' && 'fadena / 1erAño / 2doCuatrimestre / Telecomunicaciones'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            ✕
          </button>
        </div>

        {/* Content Body: 3-column layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Column 1: Curricular Tree Navigation */}
          <div className="w-64 shrink-0 border-r border-slate-800 bg-slate-950 p-3 overflow-y-auto font-mono text-xs flex flex-col">
            <div className="mb-2.5 pb-2 border-b border-slate-800/80 flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Árbol Curricular
              </span>
              <span className="text-[9px] text-slate-500">2 ramas</span>
            </div>

            <div className="space-y-1 select-none flex-1">
              {CURRICULUM_TREE.map((root) => {
                const isRootExpanded = expandedFolders.has(root.id);
                return (
                  <div key={root.id} className="space-y-0.5">
                    {/* Root Folder */}
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={() => toggleFolder(root.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          toggleFolder(root.id);
                        }
                      }}
                      className="flex items-center gap-1.5 px-2 py-1.5 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      {isRootExpanded ? (
                        <ChevronDown className="h-3.5 w-3.5 text-slate-500 group-hover:text-slate-300" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-slate-300" />
                      )}
                      {isRootExpanded ? (
                        <FolderOpen className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Folder className="h-3.5 w-3.5 text-emerald-400" />
                      )}
                      <span className="font-semibold text-slate-200">{root.name}</span>
                    </div>

                    {/* Root Subfolders */}
                    {isRootExpanded &&
                      root.subfolders?.map((sub1) => {
                        const isSub1Expanded = expandedFolders.has(sub1.id);
                        return (
                          <div key={sub1.id} className="pl-3 space-y-0.5 border-l border-slate-800/60 ml-3">
                            <div
                              role="button"
                              tabIndex={0}
                              onClick={() => toggleFolder(sub1.id)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault();
                                  toggleFolder(sub1.id);
                                }
                              }}
                              className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            >
                              {isSub1Expanded ? (
                                <ChevronDown className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                              ) : (
                                <ChevronRight className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                              )}
                              {isSub1Expanded ? (
                                <FolderOpen className="h-3 w-3 text-emerald-400/80" />
                              ) : (
                                <Folder className="h-3 w-3 text-emerald-400/80" />
                              )}
                              <span className="text-slate-300">{sub1.name}</span>
                            </div>

                            {/* Sub1 Notebooks (e.g. Fase 0) */}
                            {isSub1Expanded &&
                              sub1.notebooks?.map((nb) => {
                                const isSelected = selectedNotebook === nb.id;
                                return (
                                  <div
                                    key={nb.id}
                                    role="button"
                                    tabIndex={0}
                                    onClick={() => selectNotebook(nb.id)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        selectNotebook(nb.id);
                                      }
                                    }}
                                    className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer ml-3 transition focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                                      isSelected
                                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] font-semibold'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                                    }`}
                                  >
                                    {renderNbIcon(nb.icon)}
                                    <span className="truncate">{nb.name}</span>
                                  </div>
                                );
                              })}

                            {/* Sub1 Nested Subfolders (e.g. 2doCuatrimestre) */}
                            {isSub1Expanded &&
                              sub1.subfolders?.map((sub2) => {
                                const isSub2Expanded = expandedFolders.has(sub2.id);
                                return (
                                  <div key={sub2.id} className="pl-3 space-y-0.5 border-l border-slate-800/60 ml-2">
                                    <div
                                      role="button"
                                      tabIndex={0}
                                      onClick={() => toggleFolder(sub2.id)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                          e.preventDefault();
                                          toggleFolder(sub2.id);
                                        }
                                      }}
                                      className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    >
                                      {isSub2Expanded ? (
                                        <ChevronDown className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                                      ) : (
                                        <ChevronRight className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                                      )}
                                      {isSub2Expanded ? (
                                        <FolderOpen className="h-3 w-3 text-emerald-400/70" />
                                      ) : (
                                        <Folder className="h-3 w-3 text-emerald-400/70" />
                                      )}
                                      <span className="text-slate-300">{sub2.name}</span>
                                    </div>

                                    {/* Sub2 Notebooks */}
                                    {isSub2Expanded &&
                                      sub2.notebooks?.map((nb) => {
                                        const isSelected = selectedNotebook === nb.id;
                                        return (
                                          <div
                                            key={nb.id}
                                            role="button"
                                            tabIndex={0}
                                            onClick={() => selectNotebook(nb.id)}
                                            onKeyDown={(e) => {
                                              if (e.key === 'Enter' || e.key === ' ') {
                                                e.preventDefault();
                                                selectNotebook(nb.id);
                                              }
                                            }}
                                            className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer ml-3 transition focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                                              isSelected
                                                ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] font-semibold'
                                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                                            }`}
                                          >
                                            {renderNbIcon(nb.icon)}
                                            <span className="truncate">{nb.name}</span>
                                          </div>
                                        );
                                      })}
                                  </div>
                                );
                              })}
                          </div>
                        );
                      })}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column 2: KC Catalog of Selected Notebook */}
          <div className="w-80 shrink-0 border-r border-slate-800 bg-slate-950/60 p-4 overflow-y-auto">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                KCs del Cuaderno
              </span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 rounded px-1.5 py-0.5 font-mono">
                BKT Activo
              </span>
            </div>

            {loadingCatalog ? (
              <div className="p-4 text-center text-xs text-slate-500">Cargando catálogo...</div>
            ) : (
              <div className="space-y-2">
                {catalog?.kcs.map((kc) => (
                  <div
                    key={kc.kc_id}
                    onClick={() => handleStartStudy(kc.kc_id)}
                    className="group flex cursor-pointer flex-col rounded-lg border border-slate-800 bg-slate-900/60 p-3 transition hover:border-emerald-500/50 hover:bg-slate-800/50"
                  >
                    <div className="flex items-start justify-between">
                      <span className="text-xs font-medium text-slate-200 group-hover:text-emerald-300 leading-snug">
                        {kc.title}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 shrink-0 ml-2">
                        P(L): {kc.bkt.p_L.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                      <span>U{kc.unit} · {kc.contextual_status}</span>
                      <span className="text-slate-400 group-hover:translate-x-1 transition font-mono">Estudiar →</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Pane: Study Area */}
          <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-slate-900/30">
            {sessionStatus === 'loading' && <p role="status" className="mb-3 text-xs text-slate-400">Recuperando sesión de estudio…</p>}
            {sessionStatus === 'error' && <p role="alert" className="mb-3 rounded border border-rose-800/50 bg-rose-950/30 p-3 text-xs text-rose-200">{flowError || 'No se pudo recuperar la sesión; no se abrió otra.'}</p>}
            {sessionStatus === 'ready' && studySessionSnapshot && (
              <p role="status" className="mb-3 text-[10px] font-mono text-slate-500">
                Sesión {studySessionSnapshot.session_id} · episodio {studySessionSnapshot.episode_id || 'sin episodio activo'}
              </p>
            )}
            {flowError && sessionStatus === 'ready' && !gradingResult && (
              <p role="alert" className="mb-3 rounded border border-amber-800/50 bg-amber-950/30 p-3 text-xs text-amber-200">{flowError}</p>
            )}
            {studySessionSnapshot?.episode_id && studySessionSnapshot.episode_phase !== 'EVALUATING' && !concept && (
              <button type="button" onClick={handleExplicitResume} className="mb-3 self-start rounded border border-sky-800/50 px-3 py-2 text-xs text-sky-200">
                Reabrir explicación del episodio restaurado
              </button>
            )}
            {!concept && !exercise ? (
              <div className="m-auto flex flex-col items-center justify-center text-center max-w-md text-slate-500">
                <Sparkles className="h-12 w-12 text-slate-600 mb-3" />
                <h3 className="text-base font-semibold text-slate-300">Seleccioná un KC para comenzar</h3>
                <p className="text-xs text-slate-400 mt-1">
                  TALOS integrará evidencia multifuente validada con S4.4 y presentará un ejercicio real del corpus con grading determinista.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Concept Presentation */}
                {concept && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                      <div>
                        <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wide">
                          Explicación Integrada Multifuente
                        </span>
                        <h3 className="text-base font-bold text-slate-100">{concept.objective}</h3>
                      </div>
                      <div className="flex items-center space-x-1 text-xs text-emerald-400 bg-emerald-950/50 border border-emerald-800/40 px-2 py-1 rounded">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>S4.4: {concept.audit_verdict}</span>
                      </div>
                    </div>

                    <div className="space-y-3 text-sm leading-relaxed text-slate-300">
                      <div>
                        <span className="text-xs font-semibold text-slate-400 uppercase">Concepto Fundamental (PRIMARY):</span>
                        <p className="mt-0.5 text-slate-200">{concept.core_concept}</p>
                      </div>

                      <div>
                        <span className="text-xs font-semibold text-slate-400 uppercase">Modelo Mental (METHODOLOGICAL):</span>
                        <p className="mt-0.5 text-slate-200">{concept.mental_model}</p>
                      </div>

                      {concept.formalization && (
                        <div className="rounded-lg bg-slate-900 border border-slate-800 p-3 font-mono text-xs text-sky-300">
                          {concept.formalization}
                        </div>
                      )}

                      {concept.pitfalls && concept.pitfalls.length > 0 && (
                        <div className="rounded-lg bg-amber-950/30 border border-amber-800/30 p-3">
                          <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold">
                            <AlertTriangle className="h-4 w-4" />
                            <span>Errores Frecuentes y Puntos Críticos:</span>
                          </div>
                          <ul className="mt-1.5 list-disc pl-4 text-xs text-amber-200/80 space-y-1">
                            {concept.pitfalls.map((p, idx) => (
                              <li key={idx}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Exercise Section */}
                {exercise && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/90 p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                        Ejercicio Real del Corpus (QUALIFIABLE)
                      </span>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">
                        Formato: {exercise.exercise_type}
                      </span>
                    </div>

                    <p className="text-sm font-medium text-slate-200">{exercise.prompt}</p>

                    {exercise.exercise_type === 'MC' && exercise.options && (
                      <div className="space-y-2 pt-2">
                        {exercise.options.map((opt, idx) => {
                          const optKey = opt.trim().charAt(0);
                          return (
                            <button
                              key={idx}
                              disabled={submissionState !== 'idle'}
                              onClick={() => setUserResponse(optKey)}
                              className={`w-full text-left p-3 rounded-lg border text-xs font-medium transition ${
                                userResponse === optKey
                                  ? 'border-emerald-500 bg-emerald-950/40 text-emerald-200'
                                  : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800'
                              }`}
                            >
                              {opt}
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {exercise.exercise_type !== 'MC' && (
                      <div className="pt-2">
                        <input
                          type="text"
                          value={userResponse}
                          onChange={(e) => setUserResponse(e.target.value)}
                          disabled={submissionState !== 'idle'}
                          placeholder="Escribí tu respuesta exacta o valor numérico..."
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500"
                        />
                      </div>
                    )}

                    {!gradingResult && (
                      <div className="flex justify-end pt-2">
                        {submissionState === 'idle' || submissionState === 'submitting' ? (
                          <button
                            disabled={!userResponse.trim() || isSubmitting || sessionStatus !== 'ready'}
                            onClick={handleSendResponse}
                            className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
                          >
                            {isSubmitting ? 'Evaluando...' : 'Enviar Respuesta'}
                          </button>
                        ) : submissionState === 'unknown' ? (
                          <button
                            disabled={isSubmitting || !submittedResponse}
                            onClick={handleRetrySameAttempt}
                            className="rounded-lg bg-amber-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50"
                          >
                            {isSubmitting ? 'Reconciliando…' : 'Reintentar misma respuesta'}
                          </button>
                        ) : null}
                      </div>
                    )}

                    {(submissionState === 'unknown' || submissionState === 'incomplete' || submissionState === 'conflict') && flowError && (
                      <p role="alert" className="rounded border border-amber-800/40 bg-amber-950/30 p-3 text-xs text-amber-200">
                        {submissionState === 'incomplete' ? 'El intento quedó incompleto y no se repetirá automáticamente. ' : ''}
                        {submissionState === 'conflict' ? 'Conflicto de identidad; la respuesta no se reenviará con otra clave. ' : ''}
                        {flowError}
                      </p>
                    )}

                    {submissionState === 'ungraded' && flowError && (
                      <p role="alert" className="rounded border border-amber-800/40 bg-amber-950/30 p-3 text-xs text-amber-200">
                        Evaluación bloqueada sin mutación: {flowError}
                      </p>
                    )}

                    {/* Grading Result */}
                    {gradingResult && (
                      <div
                        className={`rounded-lg border p-4 text-xs ${
                          gradingResult.is_correct
                            ? 'border-emerald-800/60 bg-emerald-950/40 text-emerald-200'
                            : 'border-rose-800/60 bg-rose-950/40 text-rose-200'
                        }`}
                      >
                        <div className="flex items-center space-x-2 font-bold text-sm">
                          {gradingResult.is_correct ? (
                            <>
                              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                              <span>Evaluación: Correcto</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 text-rose-400" />
                              <span>Evaluación: Incorrecto</span>
                            </>
                          )}
                        </div>
                        <p className="mt-2 text-xs leading-relaxed">{gradingResult.feedback}</p>
                        {gradingResult.hint && <p className="mt-2 text-xs text-amber-200">Pista: {gradingResult.hint}</p>}

                        <div className="mt-3 flex items-center justify-between border-t border-slate-800/60 pt-3 text-[11px] text-slate-400">
                          <span>
                            BKT P(L) actualizado a:{' '}
                            <strong className="text-white font-mono">
                              {(gradingResult.p_L ?? gradingResult.bkt_update?.p_L)?.toFixed(2)}
                            </strong>{' '}
                            (Intentos: {gradingResult.attempts ?? gradingResult.bkt_update?.attempts})
                          </span>
                          {gradingResult.next_eligible_action?.recommendation && (
                            <span>
                              Próxima acción:{' '}
                              <strong className="text-emerald-400">{gradingResult.next_eligible_action.recommendation}</strong>
                            </span>
                          )}
                        </div>
                        {gradingResult.was_idempotent_replay && (
                          <p role="status" className="mt-2 text-[10px] text-sky-200">Resultado recuperado del mismo intento; no se aplicó una mutación adicional.</p>
                        )}
                        <button type="button" onClick={handleNewAttempt} className="mt-3 rounded border border-white/15 px-3 py-2 text-xs text-white/80">
                          Comenzar un intento nuevo
                        </button>
                      </div>
                    )}

                    {attemptHistory.length > 0 && (
                      <details className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
                        <summary className="cursor-pointer">Intentos previos ({attemptHistory.length})</summary>
                        <ol className="mt-2 list-inside list-decimal space-y-1">
                          {attemptHistory.map((attempt) => (
                            <li key={attempt.attemptId}>
                              {attempt.status === 'graded'
                                ? (attempt.result?.is_correct ? 'Correcto' : 'Incorrecto')
                                : attempt.status === 'ungraded' ? 'No evaluado' : 'Estado no concluyente'}
                              {attempt.result?.feedback ? ` — ${attempt.result.feedback}` : ''}
                            </li>
                          ))}
                        </ol>
                      </details>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
