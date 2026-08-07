import { useState } from 'react';
import toast from 'react-hot-toast';
import { syncEpisodes } from '../api_client';
import { Anime, EpisodesMap, Mapping } from '../types';

export function useEpisodes(
  animeDetails: Anime | null,
  setHasChanges: React.Dispatch<React.SetStateAction<boolean>>
) {
  const [episodesMap, setEpisodesMap] = useState<EpisodesMap>({ tmdb: [], tvdb: [] });
  const [totalEpisodes, setTotalEpisodes] = useState<number>(0);
  const [episodeTypes, setEpisodeTypes] = useState<Record<string, string>>({});
  const [isSyncing, setIsSyncing] = useState(false);

  const handleEpisodeTypeChange = (epIdx: number, val: string) => {
    setHasChanges(true);
    setEpisodeTypes(prev => ({ ...prev, [epIdx]: val }));
  };

  const handleSyncEpisodes = async (mappings: Mapping[], overrideId?: number) => {
    const idToUse = overrideId || animeDetails?.anilist_id;
    if (!idToUse) return;
    setIsSyncing(true);
    try {
      const res = await syncEpisodes(idToUse, mappings);
      setEpisodesMap(res.episodes);
      setTotalEpisodes(res.total_episodes);
      
      if (res.mal_fillers && Object.keys(res.mal_fillers).length > 0) {
        setEpisodeTypes(prev => {
          const next = { ...prev };
          let changed = false;
          for (const [epId, type] of Object.entries(res.mal_fillers!)) {
            if (next[epId] !== type) {
              next[epId] = type;
              changed = true;
            }
          }
          if (changed) setHasChanges(true);
          return changed ? next : prev;
        });
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to sync episodes');
    }
    setIsSyncing(false);
  };

  return {
    episodesMap, setEpisodesMap,
    totalEpisodes, setTotalEpisodes,
    episodeTypes, setEpisodeTypes,
    handleEpisodeTypeChange,
    handleSyncEpisodes,
    isSyncing
  };
}
