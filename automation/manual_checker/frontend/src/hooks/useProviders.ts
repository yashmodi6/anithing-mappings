import { useState, useEffect } from 'react';
import { autoMapAnime, getPosterPreview } from '../api_client';
import { Anime, Mapping } from '../types';

export function useProviders(
  animeDetails: Anime | null, 
  setAnimeDetails: React.Dispatch<React.SetStateAction<Anime | null>>,
  setHasChanges: React.Dispatch<React.SetStateAction<boolean>>
) {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [isAutoMapping, setIsAutoMapping] = useState<boolean>(false);
  const [fetchingPreviews, setFetchingPreviews] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (animeDetails?.mappings) {
      setMappings(animeDetails.mappings);
    } else {
      setMappings([]);
    }
  }, [animeDetails]);

  useEffect(() => {
    // Automatically fetch previews for mappings that don't have them yet
    mappings.forEach((mapping, index) => {
      if (mapping.id && !mapping._preview && !fetchingPreviews[index]) {
        fetchPreviewForMapping(index);
      }
    });
  }, [mappings]);

  const handleAddMapping = (provider: Mapping['provider']) => {
    setMappings(prev => [...prev, { provider, type: 'show', id: '', scope: provider === 'mal' || provider === 'imdb' ? undefined : 's1' }]);
    setHasChanges(true);
  };

  const handleUpdateMapping = (index: number, updates: Partial<Mapping>) => {
    setMappings(prev => {
      const next = [...prev];
      next[index] = { ...next[index], ...updates };
      return next;
    });
    setHasChanges(true);
  };

  const handleRemoveMapping = (index: number) => {
    setMappings(prev => {
      const next = [...prev];
      next.splice(index, 1);
      return next;
    });
    setHasChanges(true);
  };

  const handleAutoMap = async () => {
    if (!animeDetails) return;
    setIsAutoMapping(true);
    try {
      const res = await autoMapAnime(animeDetails.anilist_id);
      
      let changed = false;
      const nextMappings = [...mappings];
      
      // A simple automap logic: if it returns tmdb/tvdb, we add or update the first occurrence
      if (res.tmdb && res.tmdb.id) {
        const existingIdx = nextMappings.findIndex(m => m.provider === 'tmdb');
        if (existingIdx >= 0) {
          nextMappings[existingIdx].id = res.tmdb.id;
          nextMappings[existingIdx].type = res.tmdb.type;
        } else {
          nextMappings.push({ provider: 'tmdb', type: res.tmdb.type, id: res.tmdb.id, scope: res.tmdb.type === 'show' ? 's1' : undefined });
        }
        changed = true;
      }
      
      if (res.tvdb && res.tvdb.id) {
        const existingIdx = nextMappings.findIndex(m => m.provider === 'tvdb');
        if (existingIdx >= 0) {
          nextMappings[existingIdx].id = res.tvdb.id;
          nextMappings[existingIdx].type = res.tvdb.type;
        } else {
          nextMappings.push({ provider: 'tvdb', type: res.tvdb.type, id: res.tvdb.id, scope: res.tvdb.type === 'show' ? 's1' : undefined });
        }
        changed = true;
      }
      
      if (changed) {
        setMappings(nextMappings);
        setHasChanges(true);
      }
    } catch(e) {
      console.error(e);
      alert("Auto mapping failed");
    }
    setIsAutoMapping(false);
  };

  const fetchPreviewForMapping = async (index: number) => {
    const mapping = mappings[index];
    if (!mapping || !mapping.id) return;
    
    setFetchingPreviews(prev => ({ ...prev, [index]: true }));
    try {
      const isMovie = mapping.type === 'movie';
      const posterRes = await getPosterPreview(mapping.provider, String(mapping.id), isMovie);
      
      if (posterRes) {
        setMappings(prev => {
          const next = [...prev];
          next[index] = { ...next[index], _preview: posterRes, _dirty: false };
          return next;
        });
      }
    } catch(e) { 
      console.error(e); 
      alert("Failed to fetch provider details"); 
    } finally {
      setFetchingPreviews(prev => ({ ...prev, [index]: false }));
    }
  };

  return {
    mappings,
    setMappings,
    handleAddMapping,
    handleUpdateMapping,
    handleRemoveMapping,
    isAutoMapping,
    handleAutoMap,
    fetchingPreviews,
    fetchPreviewForMapping
  };
}
