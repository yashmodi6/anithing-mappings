import React from 'react';
import { Check, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { EpisodesMap } from '../../types';

interface EpisodeTableProps {
  totalEpisodes: number;
  episodesMap: EpisodesMap;
  episodeTypes: Record<string, string>;
  isSyncing: boolean;
  handleEpisodeTypeChange: (epIdx: number, val: string) => void;
  handleSync: () => void;
}

export default function EpisodeTable({ totalEpisodes, episodesMap, episodeTypes, isSyncing, handleEpisodeTypeChange, handleSync }: EpisodeTableProps) {
  let canonCount = 0;
  let fillerCount = 0;
  let mixedCount = 0;
  for (let i = 1; i <= totalEpisodes; i++) {
    const type = episodeTypes[i] || 'canon';
    if (type === 'canon') canonCount++;
    else if (type === 'filler') fillerCount++;
    else if (type === 'mixed') mixedCount++;
  }

  return (
    <section className="flex-col gap-lg animate-in" style={{ animationDelay: '0.2s' }}>
      <div className="flex-row justify-between items-center">
        <div className="flex-row items-center gap-xl">
          <h3 className="text-xl">Episode Mapping</h3>
          <div className="flex-row gap-lg text-sm font-medium">
            <span style={{color: 'var(--text-main)'}}>{canonCount} Canon</span>
            <span style={{color: '#fde047'}}>{fillerCount} Filler</span>
            <span style={{color: '#d946ef'}}>{mixedCount} Mixed</span>
          </div>
        </div>
        <button 
          className="btn btn-outline btn-sm flex-row items-center gap-sm"
          onClick={handleSync}
          disabled={isSyncing}
        >
          {isSyncing ? <Loader2 className="animate-spin" size={14} /> : <RefreshCw size={14} />}
          Sync Episodes
        </button>
      </div>

      <div className="episodes-table-wrapper" style={{ overflowX: 'auto' }}>
        <table className="episodes-table">
          <thead>
            <tr>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '60px', borderRight: '1px solid var(--border)'}}>#</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '80px', borderRight: '1px solid var(--border)'}}>Type</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '35%', borderRight: '1px solid var(--border)'}}>TMDB</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '35%', borderRight: '1px solid var(--border)'}}>TVDB</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '90px'}}>Match</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: totalEpisodes }).map((_, i) => {
              const epNum = i + 1;
              const tEp = episodesMap.tmdb[i] || {};
              const vEp = episodesMap.tvdb[i] || {};
              const epType = episodeTypes[epNum] || 'canon';
              let rowStyle = {};
              if (epType === 'filler') rowStyle = { backgroundColor: 'rgba(255, 235, 59, 0.1)' };
              if (epType === 'mixed') rowStyle = { backgroundColor: 'rgba(156, 39, 176, 0.1)' };

              const norm = (s?: string) => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '');
              const tTitle = tEp.name || tEp.title || '';
              const vTitle = vEp.name || (vEp.names && vEp.names.length > 0 ? vEp.names[0] : '');
              const isMatch = norm(tTitle) === norm(vTitle) && norm(tTitle).length > 0;

              return (
                <tr key={epNum} className="episode-row" style={rowStyle}>
                  <td className="episode-cell text-center font-medium" style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)' }}>
                    <span>{epNum}</span>
                  </td>
                  <td className="episode-cell" style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)', padding: '0 12px' }}>
                    <select 
                      value={epType}
                      onChange={(e) => handleEpisodeTypeChange(epNum, e.target.value)}
                    >
                      <option value="canon">Canon</option>
                      <option value="filler">Filler</option>
                      <option value="mixed">Mixed</option>
                    </select>
                  </td>

                  {/* TMDB */}
                  <td className="episode-cell" style={{ verticalAlign: 'top', borderRight: '1px solid var(--border)' }}>
                    <div className="flex-col gap-sm">
                      <div className="flex-row gap-md items-start" style={{ overflow: 'hidden' }}>
                        <div className="ep-card" style={{ flexShrink: 0 }}>
                          {tEp.thumbnail ? <img src={tEp.thumbnail} alt="" className="ep-thumbnail" /> : <div className="ep-thumbnail flex-row justify-center items-center text-xs text-muted">No Thumb</div>}
                        </div>
                        <span className="text-sm font-medium" style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={tTitle || "Unknown"}>
                          {tTitle || <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">S</span>
                          <input type="text" className="input-field text-center text-xs" style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }} defaultValue={tEp.season || ''} />
                        </div>
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">E</span>
                          <input type="text" className="input-field text-center text-xs" style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }} defaultValue={tEp.episode || tEp.episode_in_season || ''} />
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* TVDB */}
                  <td className="episode-cell" style={{ verticalAlign: 'top', borderRight: '1px solid var(--border)' }}>
                    <div className="flex-col gap-sm">
                      <div className="flex-row gap-md items-start" style={{ overflow: 'hidden' }}>
                        <div className="ep-card" style={{ flexShrink: 0 }}>
                          {vEp.thumbnail ? <img src={vEp.thumbnail} alt="" className="ep-thumbnail" /> : <div className="ep-thumbnail flex-row justify-center items-center text-xs text-muted">No Thumb</div>}
                        </div>
                        <span className="text-sm font-medium" style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={vTitle || "Unknown"}>
                          {vTitle || <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">S</span>
                          <input type="text" className="input-field text-center text-xs" style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }} defaultValue={vEp.season || ''} />
                        </div>
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">E</span>
                          <input type="text" className="input-field text-center text-xs" style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }} defaultValue={vEp.episode || vEp.episode_in_season || ''} />
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Match Column */}
                  <td className="episode-cell text-center" style={{ verticalAlign: 'middle' }}>
                    {isMatch 
                      ? <div className="text-success font-medium flex-row items-center justify-center gap-sm" style={{ fontSize: '11px' }}><Check size={14} /> Matched</div> 
                      : <div className="text-warning font-medium flex-row items-center justify-center gap-sm" style={{ fontSize: '11px' }}><AlertTriangle size={14} /> Mismatched</div>
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
