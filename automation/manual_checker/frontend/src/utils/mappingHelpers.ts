import { Mapping } from '../types';

/**
 * Finds the index of the first mapping for a given provider.
 * Returns -1 if not found.
 */
export function findMappingIndex(mappings: Mapping[], provider: Mapping['provider']): number {
  return mappings.findIndex(m => m.provider === provider);
}

/**
 * Merges auto-map API result (tmdb/tvdb) into the existing mappings array.
 * Mutates a copy and returns the new array plus a `changed` flag.
 */
export function mergeAutoMapResult(
  mappings: Mapping[],
  result: { tmdb?: { id: string; type: 'show' | 'movie' }; tvdb?: { id: string; type: 'show' | 'movie' } }
): { next: Mapping[]; changed: boolean } {
  const next = [...mappings];
  let changed = false;

  for (const provider of ['tmdb', 'tvdb'] as const) {
    const data = result[provider];
    if (!data?.id) continue;

    const idx = next.findIndex(m => m.provider === provider);
    const entry: Partial<Mapping> = {
      id: data.id,
      type: data.type,
      _dirty: true,
      scope: data.type === 'show' ? 's1' : undefined,
    };

    if (idx >= 0) {
      next[idx] = { ...next[idx], ...entry };
    } else {
      next.push({ provider, ...entry } as Mapping);
    }
    changed = true;
  }

  return { next, changed };
}

/**
 * Builds a new mapping entry with safe defaults for a given provider.
 */
export function buildDefaultMapping(provider: Mapping['provider']): Mapping {
  const needsScope = provider === 'tmdb' || provider === 'tvdb';
  return {
    provider,
    type: 'show',
    id: '',
    scope: needsScope ? 's1' : undefined,
  };
}
