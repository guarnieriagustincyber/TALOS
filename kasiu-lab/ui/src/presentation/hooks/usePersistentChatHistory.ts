/**
 * Hook de persistencia de historial de chat en localStorage con carga perezosa (sliding window).
 * 
 * INVARIANTES:
 * 1. Fuente de verdad epistémica: localStorage es EXCLUSIVAMENTE historial conversacional de UI.
 *    BKT, Evidence Ledger y StudySessionSnapshot permanecen soberanos en el backend.
 * 2. Aislamiento por alcance: Cada notebook o carpeta tiene su propia clave `talos_chat_history_${scopeId}`.
 * 3. Fail-Closed: Si el JSON almacenado está corrupto o es inválido, inicializa seguro con fallback sin crashear.
 * 4. Preservación de Evidencias: Mantiene intactos los arrays `evidences` (docHash, pageStart, etc.)
 *    para que las citas doctrinales [E#] funcionen fielmente al recargar.
 * 5. Límite de Almacenamiento: Recorta automáticamente a un máximo de 500 mensajes (descartando los más antiguos)
 *    para prevenir desbordamientos en la cuota de localStorage (~5MB).
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Message } from '../features/views/types';

const PAGE_SIZE = 10;
const MAX_STORED_MESSAGES = 500;

function enforceStorageLimit(messages: Message[], maxMessages = MAX_STORED_MESSAGES): Message[] {
  if (messages.length <= maxMessages) return messages;
  return messages.slice(-maxMessages);
}

export function usePersistentChatHistory(
  scopeId: string,
  initialFallbackMessages: Message[] = []
) {
  const storageKey = useMemo(() => `talos_chat_history_${scopeId}`, [scopeId]);

  // Número de mensajes visibles actualmente desde el final (ventana deslizante)
  const [windowSize, setWindowSize] = useState<number>(PAGE_SIZE);
  const [allMessages, setAllMessages] = useState<Message[]>(() => {
    try {
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(`talos_chat_history_${scopeId}`);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            return parsed;
          }
        }
      }
    } catch (err) {
      console.warn(`[TALOS Chat] Historial corrupto en talos_chat_history_${scopeId}, restableciendo a predeterminado.`, err);
    }
    return initialFallbackMessages;
  });
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Carga o inicializa el historial completo desde localStorage al cambiar de cuaderno
  useEffect(() => {
    setWindowSize(PAGE_SIZE);
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setAllMessages(parsed);
          return;
        }
      }
    } catch (err) {
      console.warn(`[TALOS Chat] Historial corrupto en ${storageKey}, restableciendo a predeterminado.`, err);
    }

    // Si no hay historial almacenado, usar mensajes iniciales de contexto
    setAllMessages(initialFallbackMessages);
    try {
      localStorage.setItem(storageKey, JSON.stringify(initialFallbackMessages));
    } catch {
      // Ignorar cuota o fallo de almacenamiento local
    }
  }, [storageKey]);

  // Mensajes visibles: los últimos `windowSize` mensajes
  const visibleMessages = useMemo(() => {
    return allMessages.slice(-windowSize);
  }, [allMessages, windowSize]);

  const totalCount = allMessages.length;
  const hasMore = windowSize < totalCount;

  // Carga más mensajes antiguos (expandir ventana hacia atrás)
  const loadMore = useCallback(() => {
    if (!hasMore || isLoadingMore) return;
    setIsLoadingMore(true);
    // Simular un micro-tick para feedback fluido en UI
    setTimeout(() => {
      setWindowSize((prev) => Math.min(totalCount, prev + PAGE_SIZE));
      setIsLoadingMore(false);
    }, 40);
  }, [hasMore, isLoadingMore, totalCount]);

  // Setter compatible con React dispatch o append directo
  const setMessages = useCallback(
    (updater: Message[] | ((prev: Message[]) => Message[])) => {
      setAllMessages((prevAll) => {
        const updated = typeof updater === 'function' ? updater(prevAll) : updater;
        const trimmed = enforceStorageLimit(updated);
        try {
          localStorage.setItem(storageKey, JSON.stringify(trimmed));
        } catch (e) {
          console.error('[TALOS Chat] Error al escribir en localStorage:', e);
        }
        const delta = trimmed.length - prevAll.length;
        if (delta > 0) {
          setWindowSize((prev) => prev + delta);
        }
        return trimmed;
      });
    },
    [storageKey]
  );

  // EDITAR un mensaje (puramente cosmético / UX, no re-envía al backend)
  const editMessage = useCallback(
    (messageId: string, newContent: string) => {
      setAllMessages((prevAll) => {
        const index = prevAll.findIndex((m) => m.id === messageId);
        if (index === -1) return prevAll;
        const updated = [...prevAll];
        updated[index] = { ...updated[index], text: newContent, edited: true };
        try {
          localStorage.setItem(storageKey, JSON.stringify(updated));
        } catch (e) {
          console.error('[TALOS Chat] Error al actualizar edición en localStorage:', e);
        }
        return updated;
      });
    },
    [storageKey]
  );

  // BORRAR un mensaje con CASCADE (borra ese + todos los posteriores en UI y localStorage)
  const deleteMessage = useCallback(
    (messageId: string) => {
      setAllMessages((prevAll) => {
        const index = prevAll.findIndex((m) => m.id === messageId);
        if (index === -1) return prevAll;
        // CASCADE: borrar desde index hasta el final
        const truncated = prevAll.slice(0, index);
        try {
          localStorage.setItem(storageKey, JSON.stringify(truncated));
        } catch (e) {
          console.error('[TALOS Chat] Error al actualizar borrado en localStorage:', e);
        }
        return truncated;
      });
    },
    [storageKey]
  );

  // LIMPIAR toda la conversación del cuaderno (solo localStorage y UI, BKT no se toca)
  const clearHistory = useCallback(() => {
    try {
      localStorage.removeItem(storageKey);
    } catch (e) {
      console.error('[TALOS Chat] Error al limpiar localStorage:', e);
    }
    setAllMessages([]);
    setWindowSize(PAGE_SIZE);
  }, [storageKey]);

  return {
    messages: visibleMessages,
    totalCount,
    hasMore,
    isLoadingMore,
    loadMore,
    setMessages,
    editMessage,
    deleteMessage,
    clearHistory,
  };
}
