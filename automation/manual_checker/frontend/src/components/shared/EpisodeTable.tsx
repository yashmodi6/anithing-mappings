import React from 'react';
import { Loader2 } from 'lucide-react';
import { EpisodesMap } from '../../types';

interface EpisodeTableProps {
  totalEpisodes: number;
  episodesMap: EpisodesMap;
  epDrafts: Record<string, string | number>;
  episodeChanges: Record<string, boolean>;
  savingEpisodes: Record<string, boolean>;
  handleEpisodeChange: (epIdx: number, provider: string, field: string, val: string) => void;
  handleEpisodeSave: (epIdx: number, provider: string) => void;
}

export default function EpisodeTable({ totalEpisodes, episodesMap, epDrafts, episodeChanges, savingEpisodes, handleEpisodeChange, handleEpisodeSave }: EpisodeTableProps) {
  return (
    <section className="flex-col gap-md animate-in" style={{ animationDelay: '0.2s' }}>
      <div className="flex-row justify-between items-start">
        <h3 className="text-xl">Episode Mapping</h3>
      </div>

      <div className="episodes-table-wrapper" style={{ overflowX: 'auto' }}>
        <table className="episodes-table">
          <thead>
            <tr>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '60px', borderRight: '1px solid var(--border)'}}>#</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '80px', borderRight: '1px solid var(--border)'}}>Type</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '40%', borderRight: '1px solid var(--border)'}}>TMDB</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{width: '40%'}}>TVDB</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: totalEpisodes }).map((_, i) => {
              const epNum = i + 1;
              const tEp = episodesMap.tmdb[i] || {};
              const vEp = episodesMap.tvdb[i] || {};
              return (
                <tr key={epNum} className="episode-row">
                  <td className="episode-cell text-center font-medium" style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)' }}>
                    <span>{epNum}</span>
                  </td>
                  <td className="episode-cell" style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)', padding: '0 12px' }}>
                    <select 
                      className="input-field" 
                      style={{ width: '100%', padding: '4px', fontSize: '11px', appearance: 'auto', backgroundColor: 'var(--surface)', textAlign: 'center' }}
                      value={epDrafts[`${epNum}_type`] || 'filler'}
                      onChange={(e) => handleEpisodeChange(epNum, 'type', '', e.target.value)}
                    >
                      <option value="filler">Filler</option>
                      <option value="canon">Canon</option>
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
                        <span className="text-sm font-medium" style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={tEp.title || "Unknown"}>
                          {tEp.title || <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row items-center gap-sm">
                          <span className="text-muted font-medium">S</span>
                          <input type="number" className="input-field input-number" style={{ width: '50px', padding: '6px' }} value={epDrafts[`${epNum}_tmdb_s`] || ''} onChange={(e) => handleEpisodeChange(epNum, 'tmdb', 's', e.target.value)} />
                        </div>
                        <div className="flex-row items-center gap-sm">
                          <span className="text-muted font-medium">E</span>
                          <input type="number" className="input-field input-number" style={{ width: '50px', padding: '6px' }} value={epDrafts[`${epNum}_tmdb_e`] || ''} onChange={(e) => handleEpisodeChange(epNum, 'tmdb', 'e', e.target.value)} />
                        </div>
                        <button 
                          className={`btn ${episodeChanges[`${epNum}_tmdb`] ? 'btn-primary' : 'btn-outline'} text-xs`} 
                          disabled={!episodeChanges[`${epNum}_tmdb`] || savingEpisodes[`${epNum}_tmdb`]}
                          onClick={() => handleEpisodeSave(epNum, 'tmdb')}
                          style={{ padding: '4px 8px', marginLeft: 'auto' }}
                        >
                          {savingEpisodes[`${epNum}_tmdb`] ? <Loader2 className="animate-spin" size={14} /> : 'Save'}
                        </button>
                      </div>
                    </div>
                  </td>

                  {/* TVDB */}
                  <td className="episode-cell" style={{ verticalAlign: 'top' }}>
                    <div className="flex-col gap-sm">
                      <div className="flex-row gap-md items-start" style={{ overflow: 'hidden' }}>
                        <div className="ep-card" style={{ flexShrink: 0 }}>
                          {vEp.thumbnail ? <img src={vEp.thumbnail} alt="" className="ep-thumbnail" /> : <div className="ep-thumbnail flex-row justify-center items-center text-xs text-muted">No Thumb</div>}
                        </div>
                        <span className="text-sm font-medium" style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={vEp.names && vEp.names.length > 0 ? vEp.names[0] : "Unknown"}>
                          {vEp.names && vEp.names.length > 0 ? vEp.names[0] : <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row items-center gap-sm">
                          <span className="text-muted font-medium">S</span>
                          <input type="number" className="input-field input-number" style={{ width: '50px', padding: '6px' }} value={epDrafts[`${epNum}_tvdb_s`] || ''} onChange={(e) => handleEpisodeChange(epNum, 'tvdb', 's', e.target.value)} />
                        </div>
                        <div className="flex-row items-center gap-sm">
                          <span className="text-muted font-medium">E</span>
                          <input type="number" className="input-field input-number" style={{ width: '50px', padding: '6px' }} value={epDrafts[`${epNum}_tvdb_e`] || ''} onChange={(e) => handleEpisodeChange(epNum, 'tvdb', 'e', e.target.value)} />
                        </div>
                        <button 
                          className={`btn ${episodeChanges[`${epNum}_tvdb`] ? 'btn-primary' : 'btn-outline'} text-xs`} 
                          disabled={!episodeChanges[`${epNum}_tvdb`] || savingEpisodes[`${epNum}_tvdb`]}
                          onClick={() => handleEpisodeSave(epNum, 'tvdb')}
                          style={{ padding: '4px 8px', marginLeft: 'auto' }}
                        >
                          {savingEpisodes[`${epNum}_tvdb`] ? <Loader2 className="animate-spin" size={14} /> : 'Save'}
                        </button>
                      </div>
                    </div>
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
