import React from 'react';
import { Loader2 } from 'lucide-react';
import InfoCard from '../shared/InfoCard';
import ProviderList from '../shared/ProviderList';
import EpisodeTable from '../shared/EpisodeTable';
import { Anime } from '../../types';

interface WorkspaceViewProps {
  animeDetails: Anime | null;
  isLoadingAnime: boolean;
  catalogState: any;
  providerState: any;
  episodeState: any;
  hasChanges: boolean;
  loadAnime: (id: number) => void;
  verifyCurrent: () => void;
  unverifyCurrent: () => void;
  skipCurrent: (reason: string) => void;
}

export default function WorkspaceView({
  animeDetails,
  isLoadingAnime,
  catalogState,
  providerState,
  episodeState,
  hasChanges,
  loadAnime,
  verifyCurrent,
  unverifyCurrent,
  skipCurrent
}: WorkspaceViewProps) {
  if (isLoadingAnime && !animeDetails) {
    return (
      <div className="flex-col items-center justify-center animate-in" style={{ height: '60vh', color: 'var(--accent)' }}>
        <Loader2 className="animate-spin" size={64} style={{ marginBottom: '16px' }} />
        <p className="text-xl font-semibold">Loading Anime Data...</p>
      </div>
    );
  }

  if (!animeDetails) return null;

  return (
    <div className="flex-col" style={{ gap: '64px' }}>
      <div className="flex-col gap-xl" style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
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
        <div className="card h-full flex-col" style={{ padding: '24px' }}>
          <ProviderList
            mappings={providerState.mappings}
            animeTitle={animeDetails.title_english || animeDetails.title_romaji || ''}
            isAutoMapping={providerState.isAutoMapping}
            fetchingPreviews={providerState.fetchingPreviews}
            handleAddMapping={providerState.handleAddMapping}
            handleUpdateMapping={providerState.handleUpdateMapping}
            handleRemoveMapping={providerState.handleRemoveMapping}
            fetchPreviewForMapping={providerState.fetchPreviewForMapping}
            handleAutoMap={providerState.handleAutoMap}
            handleReset={() => loadAnime(animeDetails.anilist_id)}
          />
        </div>
      </div>
      {!(animeDetails.format || '').toUpperCase().includes('MOVIE') && (
        <EpisodeTable
          totalEpisodes={episodeState.totalEpisodes}
          episodesMap={episodeState.episodesMap}
          episodeTypes={episodeState.episodeTypes}
          isSyncing={episodeState.isSyncing}
          handleEpisodeTypeChange={episodeState.handleEpisodeTypeChange}
          handleSync={() => episodeState.handleSyncEpisodes(providerState.mappings)}
        />
      )}
    </div>
  );
}
