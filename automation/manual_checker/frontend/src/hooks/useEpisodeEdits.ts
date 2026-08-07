import { useState, useCallback } from 'react';
import { EpisodesMap } from '../types';
import { compressEpisodesToJSON, expandJSONToEpisodes, CompressibleEpisode } from '../utils/mappingEngine';

/** A single pending edit for one episode row in one provider */
export interface EpisodeEdit {
  season: string | number;
  episode_in_season: string | number;
}

/** Dirty edits keyed by provider → globalEpNum (1-based) → edit values */
type DirtyEdits = {
  tmdb: Record<number, EpisodeEdit>;
  tvdb: Record<number, EpisodeEdit>;
};

const EMPTY: DirtyEdits = { tmdb: {}, tvdb: {} };

export function useEpisodeEdits() {
  const [dirtyEdits, setDirtyEdits] = useState<DirtyEdits>(EMPTY);

  /**
   * Stage a single field change for a provider's episode row.
   * Does NOT persist anything — only updates local dirty state.
   */
  const setDirtyEdit = useCallback(
    (
      provider: 'tmdb' | 'tvdb',
      globalEp: number,
      field: 'season' | 'episode_in_season',
      value: string
    ) => {
      setDirtyEdits(prev => ({
        ...prev,
        [provider]: {
          ...prev[provider],
          [globalEp]: {
            ...prev[provider][globalEp],
            [field]: value,
          },
        },
      }));
    },
    []
  );

  /** Clear all staged edits (call after a successful save) */
  const clearDirtyEdits = useCallback(() => {
    setDirtyEdits(EMPTY);
  }, []);

  /** True when at least one provider has at least one dirty row */
  const hasDirtyEdits =
    Object.keys(dirtyEdits.tmdb).length > 0 ||
    Object.keys(dirtyEdits.tvdb).length > 0;

  /**
   * Merges dirty edits into the existing episode_mapping JSON and recompresses.
   *
   * Instead of rebuilding all 1100+ episodes from scratch, this:
   *  1. Expands the existing episode_mapping JSON into a lookup table
   *  2. Patches ONLY the dirty rows into that lookup
   *  3. Recompresses the patched lookup back to a compact JSON string
   *
   * This is much cheaper than iterating the full episodesMap array.
   *
   * @param episodesMap - Current synced episodes (used only if no existing mapping JSON)
   * @param getExistingJSON - Returns the current episode_mapping string for a provider
   * @param updateMappingEpisodeJSON - Callback to persist the new JSON string
   */
  const commitEdits = useCallback(
    (
      episodesMap: EpisodesMap,
      onSaveEdits: (provider: 'tmdb' | 'tvdb', jsonString: string) => void,
      getExistingJSON?: (provider: 'tmdb' | 'tvdb') => string
    ) => {
      const providers: Array<'tmdb' | 'tvdb'> = ['tmdb', 'tvdb'];

      for (const provider of providers) {
        const providerDirty = dirtyEdits[provider];
        if (Object.keys(providerDirty).length === 0) continue;

        // Step 1: Expand existing JSON to a lookup of globalEp -> {season, episode_in_season}
        const existingJSON = getExistingJSON ? getExistingJSON(provider) : '';
        const lookup = expandJSONToEpisodes(existingJSON);

        // Step 2: If no existing JSON, seed the lookup from current episodesMap
        if (!existingJSON) {
          episodesMap[provider].forEach((ep, idx) => {
            const globalEp = idx + 1;
            lookup[globalEp] = {
              season: Number(ep.season ?? 0),
              episode_in_season: Number(ep.episode_in_season ?? ep.episode ?? 0),
            };
          });
        }

        // Step 3: Patch only the dirty rows — no need to touch the other 1000+ episodes
        for (const [epNumStr, edit] of Object.entries(providerDirty)) {
          const globalEp = Number(epNumStr);
          lookup[globalEp] = {
            season: Number(edit.season),
            episode_in_season: Number(edit.episode_in_season),
          };
        }

        // Step 4: Convert lookup back to CompressibleEpisode[] and compress
        const compressible: CompressibleEpisode[] = Object.entries(lookup).map(
          ([globalEpStr, slot]) => ({
            global_episode: Number(globalEpStr),
            season: slot.season,
            episode_in_season: slot.episode_in_season,
          })
        );

        const jsonString = compressEpisodesToJSON(compressible);
        onSaveEdits(provider, jsonString);
      }
    },
    [dirtyEdits]
  );

  return {
    dirtyEdits,
    setDirtyEdit,
    clearDirtyEdits,
    hasDirtyEdits,
    commitEdits,
  };
}
