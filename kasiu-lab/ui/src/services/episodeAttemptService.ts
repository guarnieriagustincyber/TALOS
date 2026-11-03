export type EpisodeAttemptStatus =
  | 'idle'
  | 'submitting'
  | 'unknown'
  | 'incomplete'
  | 'conflict'
  | 'graded'
  | 'ungraded';

export interface EpisodeAttemptEntry {
  attemptId: string;
  answer: string;
  status: Exclude<EpisodeAttemptStatus, 'idle'>;
  result?: Record<string, unknown>;
  message?: string;
}

export interface EpisodeAttemptRecord {
  version: 1;
  sessionId: string;
  episodeId: string;
  exerciseId: string;
  current: EpisodeAttemptEntry | null;
  history: EpisodeAttemptEntry[];
}

export interface EpisodeAttemptStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

export function episodeAttemptStorageKey(sessionId: string, episodeId: string, exerciseId: string): string {
  return `talos_episode_attempts:${encodeURIComponent(sessionId)}:${encodeURIComponent(episodeId)}:${encodeURIComponent(exerciseId)}`;
}

export function readEpisodeAttemptRecord(
  storage: EpisodeAttemptStorage,
  sessionId: string,
  episodeId: string,
  exerciseId: string,
): EpisodeAttemptRecord | null {
  const raw = storage.getItem(episodeAttemptStorageKey(sessionId, episodeId, exerciseId));
  if (!raw) return null;
  const record = JSON.parse(raw) as EpisodeAttemptRecord;
  const validStatuses: EpisodeAttemptStatus[] = [
    'submitting', 'unknown', 'incomplete', 'conflict', 'graded', 'ungraded',
  ];
  const isEntry = (entry: unknown): entry is EpisodeAttemptEntry => {
    if (typeof entry !== 'object' || entry === null) return false;
    const candidate = entry as Partial<EpisodeAttemptEntry>;
    return typeof candidate.attemptId === 'string' &&
      typeof candidate.answer === 'string' &&
      validStatuses.includes(candidate.status as EpisodeAttemptStatus);
  };
  if (
    record.version !== 1 || record.sessionId !== sessionId ||
    record.episodeId !== episodeId || record.exerciseId !== exerciseId ||
    !Array.isArray(record.history) ||
    !record.history.every(isEntry) ||
    (record.current !== null && !isEntry(record.current))
  ) {
    throw new Error('El registro local no coincide con la identidad de sesión, episodio y ejercicio.');
  }
  if (record.current?.status === 'submitting') {
    return { ...record, current: { ...record.current, status: 'unknown' } };
  }
  return record;
}

export function writeEpisodeAttemptRecord(
  storage: EpisodeAttemptStorage,
  record: EpisodeAttemptRecord,
): void {
  storage.setItem(
    episodeAttemptStorageKey(record.sessionId, record.episodeId, record.exerciseId),
    JSON.stringify(record),
  );
}
