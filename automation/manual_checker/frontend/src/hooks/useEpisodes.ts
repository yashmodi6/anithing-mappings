import { useState } from 'react';
import { getEpisodes } from '../api_client';
import { Anime, Episode, EpisodesMap } from '../types';

export function useEpisodes(
  animeDetails: Anime | null,
  setHasChanges: React.Dispatch<React.SetStateAction<boolean>>
) {
  const [episodesMap, setEpisodesMap] = useState<EpisodesMap>({ tmdb: [], tvdb: [] });
  const [totalEpisodes, setTotalEpisodes] = useState<number>(0);
  const [episodeChanges, setEpisodeChanges] = useState<Record<string, boolean>>({});
  const [savingEpisodes, setSavingEpisodes] = useState<Record<string, boolean>>({});
  const [epDrafts, setEpDrafts] = useState<Record<string, string | number>>({});

  const handleEpisodeChange = (epIdx: number, provider: string, field: string, val: string) => {
    setHasChanges(true);
    setEpisodeChanges(prev => ({ ...prev, [`${epIdx}_${provider}`]: true }));
    setEpDrafts(prev => ({ ...prev, [`${epIdx}_${provider}_${field}`]: val }));
  };

  const handleEpisodeSave = async (epIdx: number, pId: string, pVal: string, isMovie: boolean) => {
    if (!animeDetails) return;
    setSavingEpisodes(prev => ({ ...prev, [`${epIdx}_${pId}`]: true }));
    try {
      const mappings: any = {};
      for (let i = 1; i <= totalEpisodes; i++) {
        mappings[i] = {
          tmdb: { s: epDrafts[`${i}_tmdb_s`], e: epDrafts[`${i}_tmdb_e`] },
          tvdb: { s: epDrafts[`${i}_tvdb_s`], e: epDrafts[`${i}_tvdb_e`] }
        };
      }
      
      const epRes = await getEpisodes(pId, animeDetails.anilist_id, mappings, pVal, isMovie);
      setEpisodesMap(prev => ({ ...prev, [pId]: epRes.episodes || [] }));
      
      const newDrafts = { ...epDrafts };
      (epRes.episodes || []).forEach((ep: Episode, i: number) => {
        newDrafts[`${i+1}_${pId}_s`] = ep.season || '';
        newDrafts[`${i+1}_${pId}_e`] = ep.episode || '';
      });
      setEpDrafts(newDrafts);
      
      const newChanges = { ...episodeChanges };
      for (let i = 1; i <= totalEpisodes; i++) {
        delete newChanges[`${i}_${pId}`];
      }
      setEpisodeChanges(newChanges);
    } catch(e) {
      console.error(e);
      alert("Failed to save episode mapping");
    }
    setSavingEpisodes(prev => ({ ...prev, [`${epIdx}_${pId}`]: false }));
  };

  return {
    episodesMap, setEpisodesMap,
    totalEpisodes, setTotalEpisodes,
    episodeChanges, setEpisodeChanges,
    savingEpisodes,
    epDrafts, setEpDrafts,
    handleEpisodeChange,
    handleEpisodeSave
  };
}
