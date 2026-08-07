import React, { useState, useEffect } from 'react';
import { getAnime, verifyAnime, unverifyAnime, skipAnime } from './api_client';
import { Loader2 } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { Anime } from './types';

import { useCatalog } from './hooks/useCatalog';
import { useProviders } from './hooks/useProviders';
import { useEpisodes } from './hooks/useEpisodes';

import Header from './components/layout/Header';
import CatalogView from './components/views/CatalogView';
import WorkspaceView from './components/views/WorkspaceView';

export default function App() {
  const [currentView, setCurrentView] = useState<string>('catalog');
  const [hasChanges, setHasChanges] = useState<boolean>(false);
  const [animeDetails, setAnimeDetails] = useState<Anime | null>(null);
  const [isLoadingAnime, setIsLoadingAnime] = useState<boolean>(false);

  const catalogState = useCatalog();
  const providerState = useProviders(animeDetails, setAnimeDetails, setHasChanges);
  const episodeState = useEpisodes(animeDetails, setHasChanges);

  useEffect(() => {
    if (catalogState.animeId) {
      loadAnime(catalogState.animeId);
    }
  }, [catalogState.animeId]);

  async function loadAnime(id: number) {
    setIsLoadingAnime(true);
    try {
      setHasChanges(false);
      const details = await getAnime(id);
      setAnimeDetails(details);
      
      const total = details.released_episodes || details.episodes || 0;
      episodeState.setTotalEpisodes(total);
      
      const epTypes: Record<string, string> = {};
      for (let i = 1; i <= total; i++) {
        epTypes[i] = (details.episode_types && details.episode_types[i]) || 'canon';
      }
      episodeState.setEpisodeTypes(epTypes);

      if (details.mappings && details.mappings.length > 0) {
        episodeState.handleSyncEpisodes(details.mappings, id);
      } else {
        episodeState.setEpisodesMap({ tmdb: [], tvdb: [] });
      }
      // Images load lazily in the browser — no need to preload them here
      
    } catch (e) {
      console.error(e);
      toast.error('Failed to load anime details');
    }
    setIsLoadingAnime(false);
  }

  const handleAnimeClick = (id: number) => {
    catalogState.setAnimeId(id);
    setCurrentView('home');
  };

  const verifyCurrent = async () => {
    if (!animeDetails || isLoadingAnime) return;
    setIsLoadingAnime(true);
    try {
      const payload = {
        anilist_id: animeDetails.anilist_id,
        title: animeDetails.title_english || animeDetails.title_romaji,
        format: animeDetails.format,
        status: animeDetails.status,
        episodes: animeDetails.episodes,
        mappings: providerState.mappings,
        episode_types: episodeState.episodeTypes
      };
      
      const res = await verifyAnime(payload);
      if (res.success) {
        setHasChanges(false);
        if (res.stats) catalogState.setStats(res.stats);
        
        catalogState.setCatalog(prev => prev.map(a => 
          a.anilist_id === animeDetails.anilist_id ? { ...a, is_verified: true } : a
        ));
        
        if (!animeDetails.is_verified) {
          catalogState.goNext();
        } else {
          loadAnime(animeDetails.anilist_id);
        }
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to verify anime');
    }
    setIsLoadingAnime(false);
  };

  const unverifyCurrent = async () => {
    if (!animeDetails || isLoadingAnime) return;
    setIsLoadingAnime(true);
    try {
      const res = await unverifyAnime(animeDetails.anilist_id);
      if (res.success) {
        if (res.stats) catalogState.setStats(res.stats);
        const updatedCatalog = catalogState.catalog.map(a => 
          a.anilist_id === animeDetails.anilist_id ? { ...a, is_verified: false } : a
        );
        catalogState.setCatalog(updatedCatalog);
        await loadAnime(animeDetails.anilist_id);
      }
    } catch(e) {
      console.error(e);
      toast.error('Failed to unverify anime');
    }
    setIsLoadingAnime(false);
  };

  const skipCurrent = async (reason: string) => {
    if (!animeDetails || isLoadingAnime) return;
    setIsLoadingAnime(true);
    try {
      const res = await skipAnime(animeDetails.anilist_id, reason);
      if (res.success) {
        if (res.stats) catalogState.setStats(res.stats);
        if (catalogState.filter === 'UNVERIFIED') {
          catalogState.setCatalog(prev => prev.filter(a => a.anilist_id !== animeDetails.anilist_id));
        } else {
          catalogState.setCatalog(prev => prev.map(a => 
            a.anilist_id === animeDetails.anilist_id ? { ...a, is_skipped: true } : a
          ));
        }
        catalogState.goNext();
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to skip anime');
    }
    setIsLoadingAnime(false);
  };

  return (
    <div className="app-container">
      {/* Toast notification container — positioned top-right, dark themed */}
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1e2027', color: '#e2e8f0', border: '1px solid #2d3748' },
          error: { iconTheme: { primary: '#ef4444', secondary: '#1e2027' } },
          success: { iconTheme: { primary: '#22c55e', secondary: '#1e2027' } },
        }}
      />
      <Header
        stats={catalogState.stats}
        currentView={currentView}
        setCurrentView={setCurrentView}
      />

      <main className="flex-col" style={{ position: 'relative', minHeight: '60vh', width: '100%', padding: 'var(--space-outer)' }}>
        {isLoadingAnime && animeDetails && (
          <div style={{ position: 'fixed', top: '45%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 100 }}>
            <Loader2 className="animate-spin text-white" size={48} />
          </div>
        )}

        <div style={{ opacity: isLoadingAnime ? 0.4 : 1, pointerEvents: isLoadingAnime ? 'none' : 'auto', transition: 'opacity 0.2s ease-in-out' }}>
          {currentView === 'home' ? (
            <WorkspaceView
              animeDetails={animeDetails}
              isLoadingAnime={isLoadingAnime}
              catalogState={catalogState}
              providerState={providerState}
              episodeState={episodeState}
              hasChanges={hasChanges}
              loadAnime={loadAnime}
              verifyCurrent={verifyCurrent}
              unverifyCurrent={unverifyCurrent}
              skipCurrent={skipCurrent}
            />
          ) : currentView === 'catalog' ? (
            <CatalogView
              catalog={catalogState.catalog}
              searchQ={catalogState.searchQ}
              setSearchQ={catalogState.setSearchQ}
              filter={catalogState.filter}
              setFilter={catalogState.setFilter}
              status={catalogState.status}
              setStatus={catalogState.setStatus}
              format={catalogState.format}
              setFormat={catalogState.setFormat}
              sort={catalogState.sort}
              setSort={catalogState.setSort}
              episodesLt={catalogState.episodesLt}
              setEpisodesLt={catalogState.setEpisodesLt}
              isLoading={catalogState.isLoading}
              hasMore={catalogState.hasMore}
              loadCatalog={() => catalogState.loadCatalog(false)}
              loadMore={catalogState.loadMore}
              onAnimeClick={handleAnimeClick}
            />
          ) : (
            <div className="flex-col gap-md animate-in text-center text-muted mt-10">
              Please select an anime from the catalog.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
