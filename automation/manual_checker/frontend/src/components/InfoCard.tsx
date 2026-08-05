import React from 'react';
import { ChevronLeft, ChevronRight, RefreshCw, Check, X } from 'lucide-react';
import { Anime } from '../types';

interface InfoCardProps {
  animeDetails: Anime;
  animeId: number;
  goPrev: () => void;
  goNext: () => void;
  loadAnime: (id: number) => void;
  hasChanges: boolean;
  handleVerify: () => void;
  handleUnverify: () => void;
}

export default function InfoCard({ animeDetails, animeId, goPrev, goNext, loadAnime, hasChanges, handleVerify, handleUnverify }: InfoCardProps) {
  return (
    <div className="card animate-in flex-row gap-md items-center justify-between" style={{ padding: '12px 16px' }}>
      <div className="flex-row items-center gap-md">
        <div className="flex-row gap-sm items-center mr-2">
          <button className="btn-icon" title="Previous Anime" onClick={goPrev}><ChevronLeft size={20} /></button>
          <button className="btn-icon" title="Next Anime" onClick={goNext}><ChevronRight size={20} /></button>
        </div>
        <h2 className="text-md font-bold">{animeDetails.title || animeDetails.title_english || animeDetails.title_romaji}</h2>
        <span className="text-sm text-muted flex-row items-center gap-sm">
          <span className="badge badge-neutral">{animeDetails.format} • Episodes: {animeDetails.released_episodes || '?'} • {animeDetails.status}</span>
        </span>
      </div>
      <div className="flex-row gap-sm">
        {animeDetails.is_verified ? (
          <>
            <button className="btn btn-primary" onClick={handleVerify} disabled={!hasChanges} title={!hasChanges ? "Make changes to re-verify" : "Re-verify changes"}>
              <RefreshCw size={16} /> Re-verify
            </button>
            <button className="btn btn-secondary" onClick={handleUnverify}>
              <X size={16} /> Unverify
            </button>
          </>
        ) : (
          <button className="btn btn-primary" onClick={handleVerify}>
            <Check size={16} /> Verify
          </button>
        )}
      </div>
    </div>
  );
}
