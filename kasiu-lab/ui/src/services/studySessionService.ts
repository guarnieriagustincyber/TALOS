import { StudySessionSnapshotData } from '../presentation/features/chat/OpeningBriefView';

export const studySessionService = {
  async openSession(notebookId: string, studentId: string = 'agustin'): Promise<StudySessionSnapshotData> {
    const res = await fetch('/api/study/session/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notebook_id: notebookId, student_id: studentId }),
    });
    if (!res.ok) {
      throw new Error(`[API ERROR ${res.status}] Error al abrir sesión de estudio`);
    }
    return res.json();
  },

  async getSnapshot(sessionId: string): Promise<StudySessionSnapshotData> {
    const res = await fetch(`/api/study/session/${sessionId}/snapshot`);
    if (!res.ok) {
      throw new Error(`[API ERROR ${res.status}] Error al obtener snapshot de sesión`);
    }
    return res.json();
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
