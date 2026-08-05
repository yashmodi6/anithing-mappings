import React, { useState, useEffect } from 'react';
import { getStats, getQueue, getAnime, getEpisodes, verifyAnime, getPosterPreview, unverifyAnime } from './api';
import { Loader2 } from 'lucide-react';
import { Anime, Stats, EpisodesMap, Provider, Episode } from './types';

// Components
import Header from './components/Header';
import CatalogView from './components/CatalogView';
import InfoCard from './components/InfoCard';
import ProviderList from './components/ProviderList';
import EpisodeTable from './components/EpisodeTable';

export default function App() {
  const [currentView, setCurrentView] = useState<string>('catalog');
  const [stats, setStats] = useState<Stats>({ total_count: 0, verified_count: 0, percentage: 0 });
  const [catalog, setCatalog] = useState<Anime[]>([]);
  
  // Filters
  const [searchQ, setSearchQ] = useState<string>('');
  const [filter, setFilter] = useState<string>('UNVERIFIED');
  const [status, setStatus] = useState<string>('ALL');
  const [format, setFormat] = useState<string>('ALL');
  const [sort, setSort] = useState<string>('POPULARITY_DESC');
  const [offset, setOffset] = useState<number>(0);
  
  // Current Anime
  const [animeId, setAnimeId] = useState<number | null>(null);
  const [animeDetails, setAnimeDetails] = useState<Anime | null>(null);
  const [episodesMap, setEpisodesMap] = useState<EpisodesMap>({ tmdb: [], tvdb: [] });
  const [totalEpisodes, setTotalEpisodes] = useState<number>(0);

  // Edits
  const [hasChanges, setHasChanges] = useState<boolean>(false);
  const [providerChanges, setProviderChanges] = useState<Record<string, boolean>>({});
  const [episodeChanges, setEpisodeChanges] = useState<Record<string, boolean>>({});
  const [savingProviders, setSavingProviders] = useState<Record<string, boolean>>({});
  const [savingEpisodes, setSavingEpisodes] = useState<Record<string, boolean>>({});
  const [epDrafts, setEpDrafts] = useState<Record<string, string | number>>({});
  const [providerDrafts, setProviderDrafts] = useState<Record<string, string>>({});
  const [committedProviders, setCommittedProviders] = useState<Record<string, string>>({});
  
  // Loading State
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    loadCatalog();
  }, [filter, status, format, sort]);

  async function loadCatalog(append: boolean = false) {
    if (!append) setIsLoading(true);
    try {
      const currentOffset = append ? offset + 30 : 0;
      const data = await getQueue(filter, status, format, currentOffset, sort);
      const newQueue = data.queue || [];
      
      if (append) {
        setCatalog(prev => [...prev, ...newQueue]);
        setOffset(currentOffset);
      } else {
        setCatalog(newQueue);
        setOffset(0);
      }
      
      if (data.stats) setStats(data.stats);
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
    } catch (e) { console.error(e); return []; }
    finally {
      if (!append) setIsLoading(false);
    }
  }

  useEffect(() => {
    if (animeId) {
      loadAnime(animeId);
    }
  }, [animeId]);

  async function loadAnime(id: number) {
    setIsLoading(true);
    try {
      setHasChanges(false);
      setProviderChanges({});
      setEpisodeChanges({});
      const details = await getAnime(id);
      setAnimeDetails(details);
      
      const isMovie = (details.format || '').toUpperCase().includes('MOVIE');
      const tmdbId = isMovie ? details.tmdb_movie_id : details.tmdb_show_id;
      const tvdbId = isMovie ? details.tvdb_movie_id : details.tvdb_show_id;
      
      const initialProviders = {
        tmdb: tmdbId || '',
        tvdb: tvdbId || '',
        mal: details.mal_id || ''
      };
      
      setProviderDrafts(initialProviders);
      setCommittedProviders(initialProviders);
      
      const tmdbRes = await getEpisodes('tmdb', id);
      const tvdbRes = await getEpisodes('tvdb', id);
      
      const total = tmdbRes.total_episodes || tvdbRes.total_episodes || 0;
      setTotalEpisodes(total);
      
      const tEps = tmdbRes.episodes || [];
      const vEps = tvdbRes.episodes || [];
      
      setEpisodesMap({ tmdb: tEps, tvdb: vEps });
      
      const drafts: Record<string, string | number> = {};
      tEps.forEach((ep: Episode, i: number) => {
        drafts[`${i+1}_tmdb_s`] = ep.season || '';
        drafts[`${i+1}_tmdb_e`] = ep.episode || '';
      });
      vEps.forEach((ep: Episode, i: number) => {
        drafts[`${i+1}_tvdb_s`] = ep.season || '';
        drafts[`${i+1}_tvdb_e`] = ep.episode || '';
      });
      setEpDrafts(drafts);
    } catch (e) { console.error(e); }
    setIsLoading(false);
  }

  const handleAnimeClick = (id: number) => {
    setAnimeId(id);
    setCurrentView('home');
  };

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

  const handleProviderIdChange = (pId: string, val: string) => {
    setHasChanges(true);
    setProviderChanges(prev => ({ ...prev, [pId]: true }));
    setProviderDrafts(prev => ({ ...prev, [pId]: val }));
  };

  const handleProviderSave = async (pId: string) => {
    if (!animeDetails || pId === 'anilist') return;
    setSavingProviders(prev => ({ ...prev, [pId]: true }));
    try {
      const val = providerDrafts[pId];
      if (pId === 'tmdb' || pId === 'tvdb' || pId === 'mal') {
        const isMovie = (animeDetails.format || '').toUpperCase().includes('MOVIE');
        const posterRes = await getPosterPreview(pId, val, isMovie);
        if (posterRes.poster) {
          setAnimeDetails(prev => prev ? { ...prev, [`${pId}_poster`]: posterRes.poster } : prev);
        }
        
        if (pId !== 'mal') {
          const epRes = await getEpisodes(pId, animeDetails.anilist_id, null, val);
          setEpisodesMap(prev => ({ ...prev, [pId]: epRes.episodes || [] }));
          
          const newDrafts = { ...epDrafts };
          (epRes.episodes || []).forEach((ep: Episode, i: number) => {
            newDrafts[`${i+1}_${pId}_s`] = ep.season || '';
            newDrafts[`${i+1}_${pId}_e`] = ep.episode || '';
          });
          setEpDrafts(newDrafts);
        }
      }
      
      setCommittedProviders(prev => ({ ...prev, [pId]: val }));
      setProviderChanges(prev => ({ ...prev, [pId]: false }));
    } catch(e) { 
      console.error(e); 
      alert("Failed to fetch provider details"); 
    }
    setSavingProviders(prev => ({ ...prev, [pId]: false }));
  };

  const handleEpisodeChange = (epIdx: number, provider: string, field: string, val: string) => {
    setHasChanges(true);
    setEpisodeChanges(prev => ({ ...prev, [`${epIdx}_${provider}`]: true }));
    setEpDrafts(prev => ({ ...prev, [`${epIdx}_${provider}_${field}`]: val }));
  };

  const handleEpisodeSave = async (epIdx: number, pId: string) => {
    if (!animeDetails) return;
    setSavingEpisodes(prev => ({ ...prev, [`${epIdx}_${pId}`]: true }));
    try {
      const pVal = providerDrafts[pId];
      const mappings: any = {};
      for (let i = 1; i <= totalEpisodes; i++) {
        mappings[i] = {
          tmdb: { s: epDrafts[`${i}_tmdb_s`], e: epDrafts[`${i}_tmdb_e`] },
          tvdb: { s: epDrafts[`${i}_tvdb_s`], e: epDrafts[`${i}_tvdb_e`] }
        };
      }
      
      const epRes = await getEpisodes(pId, animeDetails.anilist_id, mappings, pVal);
      setEpisodesMap(prev => ({ ...prev, [pId]: epRes.episodes || [] }));
      
      const newDrafts = { ...epDrafts };
      (epRes.episodes || []).forEach((ep: Episode, i: number) => {
        newDrafts[`${i+1}_${pId}_s`] = ep.season || '';
        newDrafts[`${i+1}_${pId}_e`] = ep.episode || '';
      });
      setEpDrafts(newDrafts);
      
      setEpisodeChanges(prev => ({ ...prev, [`${epIdx}_${pId}`]: false }));
    } catch(e) {
      console.error(e);
      alert("Failed to update episode mapping");
    }
    setSavingEpisodes(prev => ({ ...prev, [`${epIdx}_${pId}`]: false }));
  };

  const handleVerify = async () => {
    if (!animeDetails) return;
    setIsLoading(true);
    try {
      const mappings: any = {};
      for (let i = 1; i <= totalEpisodes; i++) {
        const tmdbEp = episodesMap.tmdb[i - 1];
        const tvdbEp = episodesMap.tvdb[i - 1];

        mappings[i] = {
          tmdb: tmdbEp ? { 
            s: tmdbEp.season, 
            e: tmdbEp.episode,
            thumb: tmdbEp.thumbnail || null,
            name: tmdbEp.title || null
          } : null,
          tvdb: tvdbEp ? { 
            s: tvdbEp.season, 
            e: tvdbEp.episode,
            thumb: tvdbEp.thumbnail || null,
            name: tvdbEp.title || null
          } : null
        };
      }
      
      const isMovie = animeDetails.format && animeDetails.format.toUpperCase().includes('MOVIE');
      const payload = {
        anilist_id: animeDetails.anilist_id,
        format: animeDetails.format,
        tmdb_show_id: isMovie ? null : committedProviders.tmdb,
        tmdb_movie_id: isMovie ? committedProviders.tmdb : null,
        tvdb_show_id: isMovie ? null : committedProviders.tvdb,
        tvdb_movie_id: isMovie ? committedProviders.tvdb : null,
        mal_id: committedProviders.mal,
        episode_mappings: mappings
      };
      
      const res = await verifyAnime(payload);
      if (res.success) {
        setHasChanges(false);
        setProviderChanges({});
        setEpisodeChanges({});
        if (res.stats) setStats(res.stats);
        setCatalog(prev => prev.map(a => a.anilist_id === animeDetails.anilist_id ? { ...a, is_verified: true } : a));
        if (!animeDetails.is_verified) {
          goNext();
        } else {
          // If already verified, just reload to reflect new saved state without skipping
          loadAnime(animeDetails.anilist_id);
        }
      }
    } catch(e) {
      console.error(e);
      alert("Failed to verify");
    }
    setIsLoading(false);
  };

  const handleUnverify = async () => {
    if (!animeDetails) return;
    setIsLoading(true);
    try {
      const res = await unverifyAnime(animeDetails.anilist_id);
      if (res.success) {
        setStats(res.stats);
        const updatedCatalog = catalog.map(a => 
          a.anilist_id === animeDetails.anilist_id ? { ...a, is_verified: false } : a
        );
        setCatalog(updatedCatalog);
        await loadAnime(animeDetails.anilist_id);
      }
    } catch(e) {
      console.error(e);
      alert("Failed to unverify anime.");
    }
    setIsLoading(false);
  };

  const getProviderInfo = (): Provider[] => {
    if (!animeDetails) return [];
    return [
      { id: 'anilist', name: 'AniList', logo: 'AL', currentId: String(animeDetails.anilist_id), poster: animeDetails.anilist_poster },
      { id: 'mal', name: 'MyAnimeList', logo: 'MAL', currentId: providerDrafts.mal, poster: animeDetails.mal_poster },
      { id: 'tmdb', name: 'TMDB', logo: 'TMDB', currentId: providerDrafts.tmdb, poster: animeDetails.tmdb_poster },
      { id: 'tvdb', name: 'TVDB', logo: 'TVDB', currentId: providerDrafts.tvdb, poster: animeDetails.tvdb_poster }
    ];
  };

  return (
    <div className="app-container">
      <Header 
        stats={stats} 
        currentView={currentView} 
        setCurrentView={setCurrentView} 
      />

      <main className="container" style={{ position: 'relative', opacity: isLoading ? 0.6 : 1, pointerEvents: isLoading ? 'none' : 'auto', transition: 'opacity 0.2s ease-in-out', minHeight: '60vh' }}>
        {isLoading && (animeDetails || currentView === 'catalog') && (
          <div style={{ position: 'absolute', top: '20vh', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 50 }}>
            <Loader2 className="animate-spin text-white" size={48} />
          </div>
        )}
        
        {isLoading && !animeDetails && currentView === 'home' ? (
          <div className="flex-col items-center justify-center animate-in" style={{ height: '60vh', color: 'var(--accent)' }}>
            <Loader2 className="animate-spin" size={64} style={{ marginBottom: '16px' }} />
            <p className="text-xl font-semibold">Loading Anime Data...</p>
          </div>
        ) : currentView === 'home' && animeDetails ? (
          <>
            <InfoCard 
              animeDetails={animeDetails} 
              animeId={animeId!} 
              goPrev={goPrev} 
              goNext={goNext} 
              loadAnime={loadAnime} 
              hasChanges={hasChanges} 
              handleVerify={handleVerify} 
              handleUnverify={handleUnverify}
            />
            
            <ProviderList 
              provs={getProviderInfo()} 
              providerChanges={providerChanges} 
              savingProviders={savingProviders}
              animeTitle={animeDetails.title_english || animeDetails.title_romaji || animeDetails.title || ''} 
              handleProviderIdChange={handleProviderIdChange} 
              handleProviderSave={handleProviderSave} 
            />
            
            {!(animeDetails.format || '').toUpperCase().includes('MOVIE') && (
              <EpisodeTable 
                totalEpisodes={totalEpisodes} 
                episodesMap={episodesMap} 
                epDrafts={epDrafts} 
                episodeChanges={episodeChanges}
                savingEpisodes={savingEpisodes}
                handleEpisodeChange={handleEpisodeChange}
                handleEpisodeSave={handleEpisodeSave}
              />
            )}</>
        ) : currentView === 'catalog' ? (
          <CatalogView 
            catalog={catalog} 
            searchQ={searchQ} 
            setSearchQ={setSearchQ} 
            filter={filter} 
            setFilter={setFilter} 
            status={status} 
            setStatus={setStatus} 
            format={format} 
            setFormat={setFormat} 
            sort={sort}
            setSort={setSort}
            loadCatalog={() => loadCatalog(false)} 
            loadMore={() => loadCatalog(true)}
            handleAnimeClick={handleAnimeClick} 
          />
        ) : (
          <div className="flex-col gap-md animate-in text-center text-muted mt-10">
            Please select an anime from the catalog.
          </div>
        )}
      </main>
    </div>
  );
}
