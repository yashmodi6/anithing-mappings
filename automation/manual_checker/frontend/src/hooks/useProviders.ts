import { useState } from 'react';
import { autoMapAnime, getPosterPreview } from '../api_client';
import { Anime } from '../types';

export function useProviders(
  animeDetails: Anime | null, 
  setAnimeDetails: React.Dispatch<React.SetStateAction<Anime | null>>,
  setHasChanges: React.Dispatch<React.SetStateAction<boolean>>
) {
  const [providerChanges, setProviderChanges] = useState<Record<string, boolean>>({});
  const [savingProviders, setSavingProviders] = useState<Record<string, boolean>>({});
  const [providerDrafts, setProviderDrafts] = useState<Record<string, string>>({});
  const [providerTypes, setProviderTypes] = useState<Record<string, 'show' | 'movie'>>({});
  const [committedProviders, setCommittedProviders] = useState<Record<string, string>>({});
  const [isAutoMapping, setIsAutoMapping] = useState<boolean>(false);

  const handleProviderIdChange = (pId: string, val: string) => {
    setHasChanges(true);
    setProviderChanges(prev => ({ ...prev, [pId]: true }));
    setProviderDrafts(prev => ({ ...prev, [pId]: val }));
  };

  const handleProviderTypeChange = (pId: string, val: 'show' | 'movie') => {
    setHasChanges(true);
    setProviderChanges(prev => ({ ...prev, [pId]: true }));
    setProviderTypes(prev => ({ ...prev, [pId]: val }));
  };

  const handleAutoMap = async () => {
    if (!animeDetails) return;
    setIsAutoMapping(true);
    try {
      const res = await autoMapAnime(animeDetails.anilist_id);
      if (res.tmdb && res.tmdb.id) {
        if (res.tmdb.id !== providerDrafts['tmdb']) {
          handleProviderIdChange('tmdb', res.tmdb.id);
        }
        if (res.tmdb.type !== providerTypes['tmdb']) {
          handleProviderTypeChange('tmdb', res.tmdb.type);
        }
      }
      if (res.tvdb && res.tvdb.id) {
        if (res.tvdb.id !== providerDrafts['tvdb']) {
          handleProviderIdChange('tvdb', res.tvdb.id);
        }
        if (res.tvdb.type !== providerTypes['tvdb']) {
          handleProviderTypeChange('tvdb', res.tvdb.type);
        }
      }
    } catch(e) {
      console.error(e);
      alert("Auto mapping failed");
    }
    setIsAutoMapping(false);
  };

  const saveProviderPreview = async (pId: string) => {
    if (!animeDetails || pId === 'anilist') return null;
    setSavingProviders(prev => ({ ...prev, [pId]: true }));
    let isMovie = false;
    try {
      const val = providerDrafts[pId];
      if (pId === 'tmdb' || pId === 'tvdb' || pId === 'mal') {
        isMovie = providerTypes[pId] === 'movie';
        const posterRes = await getPosterPreview(pId, val, isMovie);
        if (posterRes.poster) {
          setAnimeDetails(prev => prev ? { ...prev, [`${pId}_poster`]: posterRes.poster } : prev);
        }
      }
      setCommittedProviders(prev => ({ ...prev, [pId]: val }));
      setProviderChanges(prev => ({ ...prev, [pId]: false }));
      
      return { val, isMovie };
    } catch(e) { 
      console.error(e); 
      alert("Failed to fetch provider details"); 
      return null;
    } finally {
      setSavingProviders(prev => ({ ...prev, [pId]: false }));
    }
  };

  return {
    providerChanges, setProviderChanges,
    savingProviders,
    providerDrafts, setProviderDrafts,
    providerTypes, setProviderTypes,
    committedProviders, setCommittedProviders,
    isAutoMapping,
    handleProviderIdChange,
    handleProviderTypeChange,
    handleAutoMap,
    saveProviderPreview
  };
}
