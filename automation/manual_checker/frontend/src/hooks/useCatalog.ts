import { useState, useEffect, useRef } from 'react';
import { getStats, getQueue } from '../api_client';
import { Anime, Stats } from '../types';

export function useCatalog() {
  const [stats, setStats] = useState<Stats>({ total_count: 0, verified_count: 0, percentage: 0 });
  const [catalog, setCatalog] = useState<Anime[]>([]);
  
  const [searchQ, setSearchQ] = useState<string>('');
  const [filter, setFilter] = useState<string>('UNVERIFIED');
  const [status, setStatus] = useState<string>('ALL');
  const [format, setFormat] = useState<string>('ALL');
  const [sort, setSort] = useState<string>('POPULARITY_DESC');
  const [episodesLt, setEpisodesLt] = useState<string>('');
  const [offset, setOffset] = useState<number>(0);
  
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [animeId, setAnimeId] = useState<number | null>(null);

  // Use a ref to track the latest offset to completely avoid stale closures in async functions
  const offsetRef = useRef(0);

  // Fetch stats once on mount
  useEffect(() => {
    getStats().then(s => setStats(s)).catch(console.error);
  }, []);

  useEffect(() => {
    loadCatalog(false);
  }, [filter, status, format, sort, episodesLt]);

  async function loadCatalog(append: boolean = false) {
    setIsLoading(true);
    try {
      const currentOffset = append ? offsetRef.current + 30 : 0;
      const data = await getQueue(filter, status, format, currentOffset, sort, searchQ, episodesLt);
      const newQueue = data.queue || [];
      
      if (append) {
        setCatalog(prev => {
          // Avoid appending duplicates by checking IDs
          const existingIds = new Set(prev.map(a => a.anilist_id));
          const uniqueNew = newQueue.filter((a: Anime) => !existingIds.has(a.anilist_id));
          return [...prev, ...uniqueNew];
        });
        offsetRef.current = currentOffset;
        setOffset(currentOffset);
      } else {
        setCatalog(newQueue);
        offsetRef.current = 0;
        setOffset(0);
      }
      
      setHasMore(data.has_more ?? newQueue.length === 30);
      if (!append) {
        if (newQueue.length > 0) {
          if (!animeId) {
            setAnimeId(newQueue[0].anilist_id);
          }
        } else {
          setAnimeId(null);
        }
      }
      return newQueue;
    } catch (e) { 
      console.error(e); 
      return []; 
    } finally {
      setIsLoading(false);
    }
  }

  const loadMore = () => loadCatalog(true);

  const goNext = async () => {
    const idx = catalog.findIndex(a => a.anilist_id === animeId);
    if (idx >= 0 && idx < catalog.length - 1) {
      setAnimeId(catalog[idx + 1].anilist_id);
    } else {
      const newItems = await loadCatalog(true);
      if (newItems.length > 0) {
        setAnimeId(newItems[0].anilist_id);
      }
    }
  };

  const goPrev = () => {
    const idx = catalog.findIndex(a => a.anilist_id === animeId);
    if (idx > 0) setAnimeId(catalog[idx - 1].anilist_id);
  };

  return {
    stats, setStats,
    catalog, setCatalog,
    searchQ, setSearchQ,
    filter, setFilter,
    status, setStatus,
    format, setFormat,
    sort, setSort,
    episodesLt, setEpisodesLt,
    isLoading,
    hasMore,
    animeId, setAnimeId,
    loadCatalog,
    loadMore,
    goNext,
    goPrev
  };
}
