import type { Citation } from "../views/types";

/** Match only a citation's explicit, namespaced identity, never its position. */
export function resolveCitationByTag(
  tag: string,
  evidences: Citation[] | undefined,
): Citation | undefined {
  const normalized = tag.trim().toUpperCase();
  if (!/^(?:E|TF|LAB)\d+$/.test(normalized)) return undefined;
  return evidences?.find((citation) => {
    const identity = citation.citationId || citation.id;
    const namespace = normalized.match(/^(?:TF|LAB|E)/)?.[0];
    return typeof identity === "string"
      && identity.trim().toUpperCase() === normalized
      && (!citation.namespace || citation.namespace === namespace);
  });
}
