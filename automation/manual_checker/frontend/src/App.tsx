import React, { useState, useEffect } from 'react';
import { getAnime, verifyAnime, unverifyAnime, getEpisodes, skipAnime } from './api_client';
import { Loader2 } from 'lucide-react';
import { Anime, Provider, Episode } from './types';

import { useCatalog } from './hooks/useCatalog';
import { useProviders } from './hooks/useProviders';
import { useEpisodes } from './hooks/useEpisodes';

import Header from './components/layout/Header';
import CatalogView from './components/views/CatalogView';
import InfoCard from './components/shared/InfoCard';
import ProviderList from './components/shared/ProviderList';
import EpisodeTable from './components/shared/EpisodeTable';

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
      providerState.setProviderChanges({});
      episodeState.setEpisodeChanges({});
      const details = await getAnime(id);
      setAnimeDetails(details);
      
      const isMovie = (details.format || '').toUpperCase().includes('MOVIE');
      const tmdbId = details.tmdb_show_id || details.tmdb_movie_id || '';
      const tvdbId = details.tvdb_show_id || details.tvdb_movie_id || '';
      
      const tmdbType = details.tmdb_movie_id ? 'movie' : (details.tmdb_show_id ? 'show' : (isMovie ? 'movie' : 'show'));
      const tvdbType = details.tvdb_movie_id ? 'movie' : (details.tvdb_show_id ? 'show' : (isMovie ? 'movie' : 'show'));
      
      const initialProviders = {
        tmdb: String(tmdbId),
        tvdb: String(tvdbId),
        mal: details.mal_id || ''
      };
      
      providerState.setProviderDrafts(initialProviders);
      providerState.setProviderTypes({ tmdb: tmdbType, tvdb: tvdbType, mal: 'show' });
      providerState.setCommittedProviders(initialProviders);
      
      const tmdbRes = await getEpisodes('tmdb', id);
      const tvdbRes = await getEpisodes('tvdb', id);
      
      const total = tmdbRes.total_episodes || tvdbRes.total_episodes || 0;
      episodeState.setTotalEpisodes(total);
      
      const tEps = tmdbRes.episodes || [];
      const vEps = tvdbRes.episodes || [];
      
      episodeState.setEpisodesMap({ tmdb: tEps, tvdb: vEps });
      
      const drafts: Record<string, string | number> = {};
      
      for (let i = 1; i <= total; i++) {
        if (details.episode_mappings && details.episode_mappings[i]) {
          drafts[`${i}_type`] = details.episode_mappings[i].type || 'filler';
        } else {
          drafts[`${i}_type`] = 'filler';
        }
      }

      tEps.forEach((ep: Episode, i: number) => {
        drafts[`${i+1}_tmdb_s`] = ep.season || '';
        drafts[`${i+1}_tmdb_e`] = ep.episode || '';
      });
      vEps.forEach((ep: Episode, i: number) => {
        drafts[`${i+1}_tvdb_s`] = ep.season || '';
        drafts[`${i+1}_tvdb_e`] = ep.episode || '';
      });
      episodeState.setEpDrafts(drafts);
      
      const postersToLoad = [
        details.anilist_poster, 
        details.mal_poster, 
        details.tmdb_poster, 
        details.tvdb_poster
      ].filter(Boolean) as string[];
      
      if (postersToLoad.length > 0) {
        await Promise.all(postersToLoad.map(url => {
          return new Promise(resolve => {
            const img = new Image();
            img.onload = resolve;
            img.onerror = resolve;
            img.src = url;
          });
        }));
      }
      
    } catch (e) { console.error(e); }
    setIsLoadingAnime(false);
  }

  const handleAnimeClick = (id: number) => {
    catalogState.setAnimeId(id);
    setCurrentView('home');
  };

  const handleProviderSaveAction = async (pId: string) => {
    const res = await providerState.saveProviderPreview(pId);
    if (res && pId !== 'mal') {
      const epRes = await getEpisodes(pId, animeDetails!.anilist_id, null, res.val, res.isMovie);
      episodeState.setEpisodesMap(prev => ({ ...prev, [pId]: epRes.episodes || [] }));
      
      const newDrafts = { ...episodeState.epDrafts };
      (epRes.episodes || []).forEach((ep: Episode, i: number) => {
        newDrafts[`${i+1}_${pId}_s`] = ep.season || '';
        newDrafts[`${i+1}_${pId}_e`] = ep.episode || '';
      });
      episodeState.setEpDrafts(newDrafts);
    }
  };

  const handleEpisodeSaveAction = async (epIdx: number, pId: string) => {
    const pVal = providerState.providerDrafts[pId];
    const isMovie = providerState.providerTypes[pId] === 'movie';
    await episodeState.handleEpisodeSave(epIdx, pId, pVal, isMovie);
  };

  const verifyCurrent = async () => {
    if (!animeDetails || isLoadingAnime) return;
    setIsLoadingAnime(true);
    try {
      const mappings: any = {};
      for (let i = 1; i <= episodeState.totalEpisodes; i++) {
        const tmdbEp = episodeState.episodesMap.tmdb[i - 1];
        const tvdbEp = episodeState.episodesMap.tvdb[i - 1];

        mappings[i] = {
          type: episodeState.epDrafts[`${i}_type`] || 'filler',
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

      const payload = {
        anilist_id: animeDetails.anilist_id,
        format: animeDetails.format,
        tmdb_show_id: providerState.providerTypes.tmdb === 'show' ? providerState.committedProviders.tmdb : null,
        tmdb_movie_id: providerState.providerTypes.tmdb === 'movie' ? providerState.committedProviders.tmdb : null,
        tvdb_show_id: providerState.providerTypes.tvdb === 'show' ? providerState.committedProviders.tvdb : null,
        tvdb_movie_id: providerState.providerTypes.tvdb === 'movie' ? providerState.committedProviders.tvdb : null,
        mal_id: providerState.committedProviders.mal,
        episode_mappings: mappings
      };
      
      const res = await verifyAnime(payload);
      if (res.success) {
        setHasChanges(false);
        providerState.setProviderChanges({});
        episodeState.setEpisodeChanges({});
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
      alert("Failed to verify anime");
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
      alert("Failed to unverify anime.");
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
        // Remove from current view if filtering by UNVERIFIED
        if (catalogState.filter === 'UNVERIFIED') {
          catalogState.setCatalog(prev => prev.filter(a => a.anilist_id !== animeDetails.anilist_id));
        } else {
          // Just move past it
          catalogState.setCatalog(prev => prev.map(a => 
            a.anilist_id === animeDetails.anilist_id ? { ...a, is_skipped: true } : a
          ));
        }
        catalogState.goNext();
      }
    } catch (e) {
      console.error(e);
      alert("Failed to skip anime");
    }
    setIsLoadingAnime(false);
  };

  const getProviderInfo = (): Provider[] => {
    if (!animeDetails) return [];
    return [
      { id: 'anilist', name: 'AniList', logo: 'AL', currentId: String(animeDetails.anilist_id), poster: animeDetails.anilist_poster },
      { id: 'mal', name: 'MyAnimeList', logo: 'MAL', currentId: providerState.providerDrafts.mal || '', poster: animeDetails.mal_poster, title: animeDetails.mal_title, date: animeDetails.mal_date },
      { id: 'tmdb', name: 'TMDB', logo: 'TMDB', currentId: providerState.providerDrafts.tmdb || '', poster: animeDetails.tmdb_poster, title: animeDetails.tmdb_title, date: animeDetails.tmdb_date },
      { id: 'tvdb', name: 'TVDB', logo: 'TVDB', currentId: providerState.providerDrafts.tvdb || '', poster: animeDetails.tvdb_poster, title: animeDetails.tvdb_title, date: animeDetails.tvdb_date }
    ];
  };

  return (
    <div className="app-container">
      <Header
        stats={catalogState.stats}
        currentView={currentView}
        setCurrentView={setCurrentView}
      />

      <main className="container" style={{ position: 'relative', minHeight: '60vh' }}>
        {isLoadingAnime && animeDetails && (
          <div style={{ position: 'fixed', top: '45%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 100 }}>
            <Loader2 className="animate-spin text-white" size={48} />
          </div>
        )}

        <div style={{ opacity: isLoadingAnime ? 0.4 : 1, pointerEvents: isLoadingAnime ? 'none' : 'auto', transition: 'opacity 0.2s ease-in-out' }}>
          {isLoadingAnime && !animeDetails && currentView === 'home' ? (
            <div className="flex-col items-center justify-center animate-in" style={{ height: '60vh', color: 'var(--accent)' }}>
              <Loader2 className="animate-spin" size={64} style={{ marginBottom: '16px' }} />
              <p className="text-xl font-semibold">Loading Anime Data...</p>
            </div>
          ) : currentView === 'home' && animeDetails ? (
            <div className="flex-col gap-md">
              <InfoCard
                animeDetails={animeDetails}
                animeId={catalogState.animeId!}
                goPrev={catalogState.goPrev}
                goNext={catalogState.goNext}
                loadAnime={loadAnime}
                hasChanges={hasChanges}
                handleVerify={verifyCurrent}
                handleUnverify={unverifyCurrent}
                handleSkip={skipCurrent}
              />
              <div className="card h-full flex-col p-0">
                <ProviderList
                  provs={getProviderInfo()}
                  providerChanges={providerState.providerChanges}
                  savingProviders={providerState.savingProviders}
                  animeTitle={animeDetails.title_english || animeDetails.title_romaji || ''}
                  providerTypes={providerState.providerTypes}
                  isAutoMapping={providerState.isAutoMapping}
                  handleProviderIdChange={providerState.handleProviderIdChange}
                  handleProviderTypeChange={providerState.handleProviderTypeChange}
                  handleProviderSave={handleProviderSaveAction}
                  handleAutoMap={providerState.handleAutoMap}
                  handleReset={() => loadAnime(animeDetails.anilist_id)}
                />
              </div>
              {!(providerState.providerTypes.tmdb === 'movie' || providerState.providerTypes.tvdb === 'movie' || (animeDetails.format || '').toUpperCase().includes('MOVIE')) && (
                <EpisodeTable
                  totalEpisodes={episodeState.totalEpisodes}
                  episodesMap={episodeState.episodesMap}
                  epDrafts={episodeState.epDrafts}
                  episodeChanges={episodeState.episodeChanges}
                  savingEpisodes={episodeState.savingEpisodes}
                  handleEpisodeChange={episodeState.handleEpisodeChange}
                  handleEpisodeSave={handleEpisodeSaveAction}
                />
              )}
            </div>
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
