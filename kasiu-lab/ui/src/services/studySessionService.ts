import { StudySessionSnapshotData } from '../presentation/features/chat/OpeningBriefView';

declare global {
  interface Window {
    __TALOS_STUDENT_ID__?: string;
    __TALOS_DEFAULT_NOTEBOOK_ID__?: string;
    __TALOS_DEFAULT_NOTEBOOK_NAME__?: string;
    __TALOS_SYNTHETIC_PROFILE__?: boolean;
  }
}

export class StudySessionRequestError extends Error {
  constructor(message: string, readonly statusCode: number) {
    super(message);
    this.name = 'StudySessionRequestError';
  }
}

export type SessionRestoreDisposition = 'RESTORED_EXISTING' | 'CREATED_NEW' | 'PREVIOUS_MISSING_CREATED_NEW';

export interface SessionRestoreResult {
  snapshot: StudySessionSnapshotData;
  disposition: SessionRestoreDisposition;
}

interface SessionIdStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

const restoreRequests = new WeakMap<object, Map<string, Promise<SessionRestoreResult>>>();

function sessionStorageKey(notebookId: string, studentId: string): string {
  return `talos_study_session:${encodeURIComponent(studentId)}:${encodeURIComponent(notebookId)}`;
}

export const studySessionService = {
  getClientStudentId(): string {
    if (typeof window !== 'undefined') {
      const configured = window.__TALOS_STUDENT_ID__;
      if (typeof configured === 'string' && configured.trim()) return configured.trim();
    }
    return 'agustin';
  },

  getStoredSessionId(
    notebookId: string,
    studentId: string = 'agustin',
    storage?: Pick<SessionIdStorage, 'getItem'>,
  ): string | null {
    try {
      const sessionIds = storage || window.localStorage;
      return sessionIds.getItem(sessionStorageKey(notebookId, studentId));
    } catch {
      return null;
    }
  },

  async openSession(notebookId: string, studentId: string = 'agustin'): Promise<StudySessionSnapshotData> {
    const res = await fetch('/api/study/session/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notebook_id: notebookId, student_id: studentId }),
    });
    if (!res.ok) {
      throw new StudySessionRequestError(`[API ERROR ${res.status}] Error al abrir sesión de estudio`, res.status);
    }
    return res.json();
  },

  async getSnapshot(sessionId: string): Promise<StudySessionSnapshotData> {
    const res = await fetch(`/api/study/session/${encodeURIComponent(sessionId)}/snapshot`);
    if (!res.ok) {
      throw new StudySessionRequestError(`[API ERROR ${res.status}] Error al obtener snapshot de sesión`, res.status);
    }
    return res.json();
  },

  async restoreOrOpenSession(
    notebookId: string,
    studentId: string = 'agustin',
    storage?: SessionIdStorage,
  ): Promise<SessionRestoreResult> {
    let sessionIds = storage;
    if (!sessionIds) {
      try {
        sessionIds = window.localStorage;
      } catch {
        throw new Error('No hay almacenamiento local disponible para conservar la identidad de sesión.');
      }
    }
    const key = sessionStorageKey(notebookId, studentId);
    let requests = restoreRequests.get(sessionIds as object);
    if (!requests) {
      requests = new Map();
      restoreRequests.set(sessionIds as object, requests);
    }
    const pending = requests.get(key);
    if (pending) return pending;

    const operation = (async (): Promise<SessionRestoreResult> => {
      const storedSessionId = sessionIds!.getItem(key);
      let previousWasMissing = false;
      if (storedSessionId) {
        try {
          const snapshot = await studySessionService.getSnapshot(storedSessionId);
          if (snapshot.notebook_id !== notebookId || snapshot.session_id !== storedSessionId) {
            throw new Error('El snapshot recuperado no coincide con la identidad de cuaderno y sesión solicitada.');
          }
          return { snapshot, disposition: 'RESTORED_EXISTING' };
        } catch (error) {
          if (!(error instanceof StudySessionRequestError) || error.statusCode !== 404) throw error;
          previousWasMissing = true;
          if (sessionIds!.getItem(key) === storedSessionId) sessionIds!.removeItem(key);
        }
      }

      const snapshot = await studySessionService.openSession(notebookId, studentId);
      if (snapshot.notebook_id !== notebookId || !snapshot.session_id) {
        throw new Error('El servidor devolvió una identidad de sesión o cuaderno inválida.');
      }
      sessionIds!.setItem(key, snapshot.session_id);
      return {
        snapshot,
        disposition: previousWasMissing ? 'PREVIOUS_MISSING_CREATED_NEW' : 'CREATED_NEW',
      };
    })();
    requests.set(key, operation);
    try {
      return await operation;
    } finally {
      if (requests.get(key) === operation) requests.delete(key);
    }
  },

  async executeAction(
    sessionId: string,
    action: string,
    payload?: Record<string, any>
  ): Promise<StudySessionSnapshotData> {
    const res = await fetch(`/api/study/session/${sessionId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, payload: payload || null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `[API ERROR ${res.status}] Error al ejecutar acción`);
    }
    return res.json();
  },
};
