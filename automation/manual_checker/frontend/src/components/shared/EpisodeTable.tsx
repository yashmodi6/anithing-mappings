import React, { useMemo, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Check, AlertTriangle, Loader2, RefreshCw, Save } from 'lucide-react';
import { EpisodesMap } from '../../types';
import { titlesMatch } from '../../utils/titleMatcher';
import { useEpisodeEdits } from '../../hooks/useEpisodeEdits';

interface EpisodeTableProps {
  totalEpisodes: number;
  episodesMap: EpisodesMap;
  episodeTypes: Record<string, string>;
  isSyncing: boolean;
  handleEpisodeTypeChange: (epIdx: number, val: string) => void;
  handleSync: () => void;
  /** Called when the user commits staged edits; receives provider + compressed JSON string */
  onSaveEdits: (provider: 'tmdb' | 'tvdb', jsonString: string) => void;
}

export default function EpisodeTable({
  totalEpisodes,
  episodesMap,
  episodeTypes,
  isSyncing,
  handleEpisodeTypeChange,
  handleSync,
  onSaveEdits,
}: EpisodeTableProps) {
  const { dirtyEdits, setDirtyEdit, clearDirtyEdits, hasDirtyEdits, commitEdits } =
    useEpisodeEdits();

  /** Ref attached to the scrollable table wrapper — required by the virtualizer */
  const tableScrollRef = useRef<HTMLDivElement>(null);

  /**
   * Row virtualizer: only renders the rows visible in the viewport + a small overscan buffer.
   * Each estimated row height is 80px — the virtualizer adjusts dynamically after first render.
   */
  const rowVirtualizer = useVirtualizer({
    count: totalEpisodes,
    getScrollElement: () => tableScrollRef.current,
    estimateSize: () => 80,
    overscan: 10,
  });

  /**
   * Cache title-match results for every visible row.
   * titlesMatch() runs our mathematical vector match on every pair — memoizing this means it
   * only recomputes when the episodesMap actually changes, not on every
   * type-dropdown click, dirty-edit keystroke, etc.
   */
  const titleMatchCache = useMemo(() => {
    const cache: Record<number, boolean> = {};
    for (let i = 0; i < totalEpisodes; i++) {
      const epNum = i + 1;
      const tTitle = (episodesMap.tmdb[i]?.name || episodesMap.tmdb[i]?.title || '') as string;
      const vEp = episodesMap.tvdb[i];
      const vTitle = (vEp?.name || (Array.isArray(vEp?.names) && vEp.names.length > 0 ? vEp.names![0] : '') || '') as string;
      cache[epNum] = titlesMatch(tTitle, vTitle);
    }
    return cache;
  }, [episodesMap, totalEpisodes]);

  let canonCount = 0;
  let fillerCount = 0;
  let mixedCount = 0;
  for (let i = 1; i <= totalEpisodes; i++) {
    const type = episodeTypes[i] || 'canon';
    if (type === 'canon') canonCount++;
    else if (type === 'filler') fillerCount++;
    else if (type === 'mixed') mixedCount++;
  }

  /** How many rows have at least one dirty field */
  const dirtyRowCount =
    new Set([
      ...Object.keys(dirtyEdits.tmdb).map(Number),
      ...Object.keys(dirtyEdits.tvdb).map(Number),
    ]).size;

  const handleSaveAll = () => {
    commitEdits(episodesMap, onSaveEdits);
    clearDirtyEdits();
  };

  const handleSaveRow = (_epNum: number) => {
    // commitEdits already filters to only providers with dirty keys
    commitEdits(episodesMap, onSaveEdits);
    clearDirtyEdits();
  };

  return (
    <section className="flex-col gap-lg animate-in" style={{ animationDelay: '0.2s' }}>
      <div className="flex-row justify-between items-center">
        <div className="flex-row items-center gap-xl">
          <h3 className="text-xl">Episode Mapping</h3>
          <div className="flex-row gap-lg text-sm font-medium">
            <span style={{ color: 'var(--text-main)' }}>{canonCount} Canon</span>
            <span style={{ color: '#fde047' }}>{fillerCount} Filler</span>
            <span style={{ color: '#d946ef' }}>{mixedCount} Mixed</span>
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

      {/* Fixed-height scroll container — the virtualizer needs a bounded scroll area */}
      <div
        ref={tableScrollRef}
        className="episodes-table-wrapper"
        style={{ overflowX: 'auto', overflowY: 'auto', height: '600px', position: 'relative' }}
      >
        {/*
          table-layout: fixed + colgroup: single source of truth for all 5 column widths.
          Rows stay in normal table flow (spacer-based virtualization), so the browser
          respects these widths perfectly on every row.
        */}
        <table className="episodes-table" style={{ width: '100%', tableLayout: 'fixed' }}>
          {/* Single source of truth for column widths */}
          <colgroup>
            <col style={{ width: '60px' }} />   {/* # */}
            <col style={{ width: '90px' }} />   {/* Type */}
            <col />                             {/* TMDB — takes remaining half */}
            <col />                             {/* TVDB — takes remaining half */}
            <col style={{ width: '90px' }} />   {/* Match */}
          </colgroup>
          <thead style={{ position: 'sticky', top: 0, zIndex: 2, background: 'var(--surface)' }}>
            <tr>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{ borderRight: '1px solid var(--border)' }}>#</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{ borderRight: '1px solid var(--border)' }}>Type</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{ borderRight: '1px solid var(--border)' }}>TMDB</th>
              <th className="text-center text-sm text-muted pb-4 px-4" style={{ borderRight: '1px solid var(--border)' }}>TVDB</th>
              <th className="text-center text-sm text-muted pb-4 px-4">Match</th>
            </tr>
          </thead>
          {/* Spacer-based virtualization: rows stay in normal table flow so colgroup widths work.
              A top spacer row holds the space above visible rows; a bottom spacer row holds the
              space below. The browser treats it as a real table and all columns align perfectly. */}
          <tbody>
            {/* Top spacer — represents all rows above the visible window */}
            {rowVirtualizer.getVirtualItems().length > 0 && rowVirtualizer.getVirtualItems()[0].start > 0 && (
              <tr style={{ height: `${rowVirtualizer.getVirtualItems()[0].start}px` }}>
                <td colSpan={5} />
              </tr>
            )}

            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const i = virtualRow.index;
              const epNum = i + 1;
              const tEp = episodesMap.tmdb[i] || {};
              const vEp = episodesMap.tvdb[i] || {};
              const epType = episodeTypes[epNum] || 'canon';

              let rowStyle: React.CSSProperties = {};
              if (epType === 'filler') rowStyle = { backgroundColor: 'rgba(255, 235, 59, 0.1)' };
              if (epType === 'mixed') rowStyle = { backgroundColor: 'rgba(156, 39, 176, 0.1)' };

              const tTitle = tEp.name || tEp.title || '';
              const vTitle = vEp.name || (vEp.names && vEp.names.length > 0 ? vEp.names[0] : '');
              // Use the pre-computed memo cache — avoids running fuzzball on every render
              const isMatch = titleMatchCache[epNum] ?? false;

              // Determine whether this row is dirty in either provider
              const isRowDirty =
                dirtyEdits.tmdb[epNum] !== undefined ||
                dirtyEdits.tvdb[epNum] !== undefined;

              if (isRowDirty) {
                rowStyle = { ...rowStyle, borderLeft: '3px solid #fbbf24' };
              }

              // Controlled values: prefer dirty edit, fall back to synced episode data
              const tmdbSeason = dirtyEdits.tmdb[epNum]?.season ?? tEp.season ?? '';
              const tmdbEp = dirtyEdits.tmdb[epNum]?.episode_in_season ?? tEp.episode_in_season ?? tEp.episode ?? '';
              const tvdbSeason = dirtyEdits.tvdb[epNum]?.season ?? vEp.season ?? '';
              const tvdbEp = dirtyEdits.tvdb[epNum]?.episode_in_season ?? vEp.episode_in_season ?? vEp.episode ?? '';

              return (
                <tr key={epNum} className="episode-row" style={rowStyle}>
                  <td
                    className="episode-cell text-center font-medium"
                    style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)' }}
                  >
                    <span>{epNum}</span>
                  </td>
                  <td
                    className="episode-cell"
                    style={{ verticalAlign: 'middle', borderRight: '1px solid var(--border)', padding: '0 12px' }}
                  >
                    <select
                      value={epType}
                      onChange={(e) => handleEpisodeTypeChange(epNum, e.target.value)}
                    >
                      <option value="canon">Canon</option>
                      <option value="filler">Filler</option>
                      <option value="mixed">Mixed</option>
                      <option value="recap">Recap</option>
                    </select>
                  </td>

                  {/* TMDB */}
                  <td className="episode-cell" style={{ verticalAlign: 'top', borderRight: '1px solid var(--border)' }}>
                    <div className="flex-col gap-sm">
                      <div className="flex-row gap-md items-start" style={{ overflow: 'hidden' }}>
                        <div className="ep-card" style={{ flexShrink: 0 }}>
                          {tEp.thumbnail
                            ? <img src={tEp.thumbnail} alt="" className="ep-thumbnail" />
                            : <div className="ep-thumbnail flex-row justify-center items-center text-xs text-muted">No Thumb</div>}
                        </div>
                        <span
                          className="text-sm font-medium"
                          style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', overflowWrap: 'break-word', wordBreak: 'break-word' }}
                          title={tTitle || 'Unknown'}
                        >
                          {tTitle || <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">S</span>
                          <input
                            type="text"
                            className="input-field text-center text-xs"
                            style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }}
                            value={String(tmdbSeason)}
                            onChange={(e) => setDirtyEdit('tmdb', epNum, 'season', e.target.value)}
                          />
                        </div>
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">E</span>
                          <input
                            type="text"
                            className="input-field text-center text-xs"
                            style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }}
                            value={String(tmdbEp)}
                            onChange={(e) => setDirtyEdit('tmdb', epNum, 'episode_in_season', e.target.value)}
                          />
                        </div>
                        {/* Single-row save icon — shown only when this row is dirty */}
                        {isRowDirty && dirtyRowCount === 1 && (
                          <button
                            title="Save this row"
                            onClick={() => handleSaveRow(epNum)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#fbbf24', padding: '2px', display: 'flex', alignItems: 'center' }}
                          >
                            <Save size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* TVDB */}
                  <td className="episode-cell" style={{ verticalAlign: 'top', borderRight: '1px solid var(--border)' }}>
                    <div className="flex-col gap-sm">
                      <div className="flex-row gap-md items-start" style={{ overflow: 'hidden' }}>
                        <div className="ep-card" style={{ flexShrink: 0 }}>
                          {vEp.thumbnail
                            ? <img src={vEp.thumbnail} alt="" className="ep-thumbnail" />
                            : <div className="ep-thumbnail flex-row justify-center items-center text-xs text-muted">No Thumb</div>}
                        </div>
                        <span
                          className="text-sm font-medium"
                          style={{ textAlign: 'left', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', overflowWrap: 'break-word', wordBreak: 'break-word' }}
                          title={vTitle || 'Unknown'}
                        >
                          {vTitle || <span className="text-muted">Unknown</span>}
                        </span>
                      </div>
                      <div className="flex-row gap-sm text-xs mt-1 items-center">
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">S</span>
                          <input
                            type="text"
                            className="input-field text-center text-xs"
                            style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }}
                            value={String(tvdbSeason)}
                            onChange={(e) => setDirtyEdit('tvdb', epNum, 'season', e.target.value)}
                          />
                        </div>
                        <div className="flex-row gap-xs items-center">
                          <span className="text-muted text-xs font-semibold">E</span>
                          <input
                            type="text"
                            className="input-field text-center text-xs"
                            style={{ width: '36px', padding: '2px', height: '24px', borderRadius: '4px' }}
                            value={String(tvdbEp)}
                            onChange={(e) => setDirtyEdit('tvdb', epNum, 'episode_in_season', e.target.value)}
                          />
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

            {/* Bottom spacer — represents all rows below the visible window */}
            {(() => {
              const items = rowVirtualizer.getVirtualItems();
              if (items.length === 0) return null;
              const lastItem = items[items.length - 1];
              const remaining = rowVirtualizer.getTotalSize() - lastItem.end;
              return remaining > 0 ? (
                <tr style={{ height: `${remaining}px` }}><td colSpan={5} /></tr>
              ) : null;
            })()}
          </tbody>
        </table>
      </div>

      {/* Floating Save All button — shown when 2+ rows are dirty */}
      {hasDirtyEdits && dirtyRowCount > 1 && (
        <button
          onClick={handleSaveAll}
          style={{
            position: 'fixed',
            bottom: '32px',
            right: '32px',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 22px',
            borderRadius: '999px',
            border: '1px solid var(--accent)',
            background: 'var(--surface-overlay, #1e2027)',
            color: 'var(--accent)',
            fontWeight: 700,
            fontSize: '14px',
            cursor: 'pointer',
            boxShadow: '0 0 0 0 var(--accent)',
            animation: 'saveAllPulse 2s infinite',
          }}
        >
          <Save size={16} />
          Save All Changes ({dirtyRowCount} rows)
        </button>
      )}

      {/* Keyframe for the pulsing glow effect */}
      <style>{`
        @keyframes saveAllPulse {
          0%   { box-shadow: 0 0 6px 0 var(--accent, #6366f1); }
          50%  { box-shadow: 0 0 18px 4px var(--accent, #6366f1); }
          100% { box-shadow: 0 0 6px 0 var(--accent, #6366f1); }
        }
      `}</style>
    </section>
  );
}
