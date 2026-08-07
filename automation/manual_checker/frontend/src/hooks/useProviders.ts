import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { autoMapAnime, getPosterPreview } from '../api_client';
import { Anime, Mapping } from '../types';
import { mergeAutoMapResult, buildDefaultMapping } from '../utils/mappingHelpers';

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
      if (mapping.id && !mapping._preview && !mapping._dirty && !fetchingPreviews[index]) {
        fetchPreviewForMapping(index);
      }
    });
  }, [mappings]);

  const handleAddMapping = (provider: Mapping['provider']) => {
    setMappings(prev => [...prev, buildDefaultMapping(provider)]);
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
      const { next, changed } = mergeAutoMapResult(mappings, res);
      if (changed) {
        setMappings(next);
        setHasChanges(true);
      }
    } catch (e) {
      console.error(e);
      toast.error('Auto mapping failed');
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
    } catch (e) {
      console.error(e);
      toast.error('Failed to fetch provider details');
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
