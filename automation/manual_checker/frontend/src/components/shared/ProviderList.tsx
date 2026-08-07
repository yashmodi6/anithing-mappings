import React, { useState } from 'react';
import { Search, Loader2, RotateCcw, Plus, Trash2, CheckCircle2, Save, Code2 } from 'lucide-react';
import { Mapping } from '../../types';

interface ProviderListProps {
  mappings: Mapping[];
  animeTitle: string;
  isAutoMapping?: boolean;
  fetchingPreviews: Record<number, boolean>;
  handleAddMapping: (provider: Mapping['provider']) => void;
  handleUpdateMapping: (index: number, updates: Partial<Mapping>) => void;
  handleRemoveMapping: (index: number) => void;
  fetchPreviewForMapping: (index: number) => void;
  handleAutoMap?: () => void;
  handleReset?: () => void;
}

export default function ProviderList({
  mappings,
  animeTitle,
  isAutoMapping,
  fetchingPreviews,
  handleAddMapping,
  handleUpdateMapping,
  handleRemoveMapping,
  fetchPreviewForMapping,
  handleAutoMap,
  handleReset,
}: ProviderListProps) {
  /**
   * Tracks which mapping rows have their Raw JSON editor open.
   * Keyed by globalIndex (the mapping's position in the mappings array).
   */
  const [jsonEditorOpen, setJsonEditorOpen] = useState<Record<number, boolean>>({});

  /**
   * Local textarea values for the JSON editor, keyed by globalIndex.
   * Uncontrolled: initialised when editor is opened, updated on change.
   */
  const [jsonEditorValues, setJsonEditorValues] = useState<Record<number, string>>({});

  const handleSearch = (providerId: string) => {
    const q = encodeURIComponent(animeTitle);
    let url = '';
    switch (providerId) {
      case 'mal':  url = `https://myanimelist.net/anime.php?q=${q}&cat=anime`; break;
      case 'tmdb': url = `https://www.themoviedb.org/search?query=${q}`; break;
      case 'tvdb': url = `https://thetvdb.com/search?query=${q}`; break;
      case 'imdb': url = `https://www.imdb.com/find?q=${q}`; break;
    }
    if (url) window.open(url, '_blank');
  };

  const toggleJsonEditor = (globalIndex: number, currentValue: string) => {
    setJsonEditorOpen(prev => {
      const isOpen = prev[globalIndex];
      if (!isOpen) {
        // Initialise the textarea with the current episode_mapping value
        setJsonEditorValues(v => ({ ...v, [globalIndex]: currentValue }));
      }
      return { ...prev, [globalIndex]: !isOpen };
    });
  };

  const handleSaveJson = (globalIndex: number) => {
    const value = jsonEditorValues[globalIndex] ?? '';
    // Persist the raw JSON string as episode_mapping
    handleUpdateMapping(globalIndex, { episode_mapping: value });
    // Close the editor
    setJsonEditorOpen(prev => ({ ...prev, [globalIndex]: false }));
  };

  const renderProviderSection = (providerId: Mapping['provider']) => {
    const providerMappings = mappings
      .map((m, idx) => ({ ...m, globalIndex: idx }))
      .filter(m => m.provider === providerId);

    return (
      <div
        className="flex-col gap-sm"
        style={{ border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', background: 'var(--surface-overlay)' }}
      >
        <div className="flex-row justify-between items-center mb-2">
          <div className="font-semibold text-lg" style={{ textTransform: 'uppercase' }}>
            {providerId}
          </div>
          <button className="btn-icon" title="Search" onClick={() => handleSearch(providerId)}>
            <Search size={16} />
          </button>
        </div>

        {providerMappings.length === 0 ? (
          <div className="text-muted text-sm text-center" style={{ padding: '8px' }}>No mappings added yet.</div>
        ) : (
          <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '12px', minWidth: '180px' }}>
            <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
              <div style={{ width: '160px' }}>
                {(providerMappings.find(m => m._preview?.poster) || providerMappings[0])._preview?.poster ? (
                  <img
                    src={(providerMappings.find(m => m._preview?.poster) || providerMappings[0])._preview!.poster}
                    alt="Poster"
                    style={{ width: '100%', height: '240px', objectFit: 'cover', borderRadius: '6px', boxShadow: '0 4px 8px rgba(0,0,0,0.4)' }}
                  />
                ) : (
                  <div style={{ width: '100%', height: '240px', background: 'var(--border)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: 'var(--text-muted)' }}>No Img</div>
                )}
              </div>
            </div>

            <div style={{ textAlign: 'center', minHeight: '40px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              {(providerMappings.find(m => m._preview?.title) || providerMappings[0])._preview?.title ? (
                <div className="text-sm font-medium" style={{ color: 'var(--text-main)', lineHeight: '1.2' }}>
                  {(providerMappings.find(m => m._preview?.title) || providerMappings[0])._preview!.title}
                  <div className="text-muted text-xs mt-1">{(providerMappings.find(m => m._preview?.date) || providerMappings[0])._preview?.date}</div>
                </div>
              ) : (
                <div className="text-sm font-medium text-muted italic">No Preview</div>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {providerMappings.map((m) => {
                const isJsonOpen = jsonEditorOpen[m.globalIndex] ?? false;

                return (
                  <div
                    key={m.globalIndex}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                      paddingTop: '8px',
                      borderTop: m.globalIndex !== providerMappings[0].globalIndex ? '1px solid var(--border)' : 'none',
                    }}
                  >
                    {/* Primary row: type selector + ID input + action buttons */}
                    <div style={{ display: 'flex', flexDirection: 'row', gap: '8px', alignItems: 'center' }}>
                      {(providerId === 'tmdb' || providerId === 'tvdb') && (
                        <select
                          className="select select-sm"
                          value={m.type}
                          onChange={(e) =>
                            handleUpdateMapping(m.globalIndex, {
                              type: e.target.value as 'show' | 'movie',
                              scope: e.target.value === 'show' ? 's1' : undefined,
                            })
                          }
                          style={{ background: '#2a2d33', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: '4px', color: 'var(--text-main)', width: '90px', flexShrink: 0 }}
                        >
                          <option value="show">TV Show</option>
                          <option value="movie">Movie</option>
                        </select>
                      )}
                      <input
                        type="text"
                        className="input-field input-sm"
                        style={{ flex: 1, padding: '6px 12px', background: '#2a2d33', border: '1px solid var(--border)' }}
                        placeholder="Provider ID"
                        value={m.id}
                        onChange={(e) => handleUpdateMapping(m.globalIndex, { id: e.target.value, _dirty: true })}
                      />

                      {/* Raw JSON toggle button — only for tmdb/tvdb */}
                      {(providerId === 'tmdb' || providerId === 'tvdb') && m.type === 'show' && (
                        <button
                          className="btn btn-sm btn-secondary flex-row items-center justify-center"
                          title={isJsonOpen ? 'Close Raw JSON editor' : 'Edit Raw JSON mapping'}
                          style={{
                            padding: '0',
                            height: '32px',
                            width: '32px',
                            flexShrink: 0,
                            borderRadius: '8px',
                            background: isJsonOpen ? 'rgba(99,102,241,0.15)' : '#2a2d33',
                            border: `1px solid ${isJsonOpen ? 'var(--accent)' : 'var(--border)'}`,
                            color: isJsonOpen ? 'var(--accent)' : 'var(--text-muted)',
                            transition: 'all 0.2s',
                          }}
                          onClick={() => toggleJsonEditor(m.globalIndex, m.episode_mapping || '')}
                        >
                          <Code2 size={14} />
                        </button>
                      )}

                      <button
                        className={`btn btn-sm flex-row items-center justify-center ${m._dirty ? 'btn-primary' : 'btn-secondary'} ${fetchingPreviews[m.globalIndex] || !m.id ? 'opacity-50' : ''}`}
                        title="Check / Fetch Preview"
                        style={{
                          padding: '0',
                          height: '32px',
                          width: '32px',
                          flexShrink: 0,
                          borderRadius: '8px',
                          transition: 'all 0.2s',
                          background: !m._dirty ? '#2a2d33' : undefined,
                          border: !m._dirty ? '1px solid var(--border)' : undefined,
                        }}
                        onClick={() => fetchPreviewForMapping(m.globalIndex)}
                        disabled={fetchingPreviews[m.globalIndex] || !m.id}
                      >
                        {fetchingPreviews[m.globalIndex] ? <Loader2 className="animate-spin" size={14} /> : <CheckCircle2 size={16} />}
                      </button>
                      <button
                        className="btn btn-sm btn-secondary flex-row items-center justify-center hover:bg-red-500/10"
                        title="Remove Mapping"
                        style={{ padding: '0', height: '32px', width: '32px', flexShrink: 0, borderRadius: '8px', background: '#2a2d33', border: '1px solid var(--border)', color: '#ef4444' }}
                        onClick={() => handleRemoveMapping(m.globalIndex)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    {/* Inline episode_mapping text input (existing) */}
                    {(providerId === 'tmdb' || providerId === 'tvdb') && m.type === 'show' && (
                      <div style={{ display: 'flex', flexDirection: 'row', gap: '8px', alignItems: 'center' }}>
                        <input
                          type="text"
                          className="input-field input-sm"
                          style={{ flex: 1, padding: '6px 12px', background: '#2a2d33', border: '1px solid var(--border)' }}
                          placeholder='Episode Mapping (e.g. {"1-12": "1-12"})'
                          value={m.episode_mapping || ''}
                          onChange={(e) => handleUpdateMapping(m.globalIndex, { episode_mapping: e.target.value })}
                        />
                      </div>
                    )}

                    {/* Raw JSON textarea editor — toggled by the </> button */}
                    {isJsonOpen && (
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          padding: '10px',
                          background: '#1a1d22',
                          borderRadius: '6px',
                          border: '1px solid var(--accent)',
                        }}
                      >
                        {/* Note: saving JSON takes effect on next Sync Episodes */}
                        <p className="text-xs text-muted" style={{ margin: 0 }}>
                          ℹ️ Saving JSON will take effect on next Sync Episodes
                        </p>
                        <textarea
                          rows={6}
                          spellCheck={false}
                          style={{
                            width: '100%',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            background: '#0d0f12',
                            color: 'var(--text-main)',
                            border: '1px solid var(--border)',
                            borderRadius: '4px',
                            padding: '8px',
                            resize: 'vertical',
                            outline: 'none',
                          }}
                          value={jsonEditorValues[m.globalIndex] ?? ''}
                          onChange={(e) =>
                            setJsonEditorValues(prev => ({ ...prev, [m.globalIndex]: e.target.value }))
                          }
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                          <button
                            className="btn btn-sm btn-primary flex-row items-center gap-sm"
                            style={{ padding: '6px 14px', borderRadius: '6px', fontSize: '12px' }}
                            onClick={() => handleSaveJson(m.globalIndex)}
                          >
                            <Save size={13} />
                            Save JSON
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '12px' }}>
          <button
            className="btn btn-sm btn-primary flex-row items-center justify-center shadow-lg"
            style={{ width: '48px', height: '32px', borderRadius: '16px', background: '#3b82f6', border: 'none' }}
            onClick={() => handleAddMapping(providerId)}
            title={`Add another ${providerId.toUpperCase()} ID`}
          >
            <Plus size={24} color="white" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <section className="flex-col gap-md animate-in" style={{ animationDelay: '0.1s' }}>
      <div className="flex-row justify-between items-center mb-2">
        <h3 className="text-xl">Provider Mappings</h3>
        <div className="flex-row gap-sm">
          {handleReset && (
            <button
              className="btn btn-secondary btn-sm flex-row gap-sm items-center text-muted"
              onClick={handleReset}
              title="Reset all fields to database defaults"
            >
              <RotateCcw size={14} />
              Reset
            </button>
          )}
          {handleAutoMap && (
            <button
              className="btn btn-secondary btn-sm flex-row gap-sm items-center"
              onClick={handleAutoMap}
              disabled={isAutoMapping}
            >
              {isAutoMapping && <Loader2 className="animate-spin" size={14} />}
              Auto Map
            </button>
          )}
        </div>
      </div>

      <div className="flex-row gap-lg" style={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '320px' }}>{renderProviderSection('tmdb')}</div>
        <div style={{ flex: 1, minWidth: '320px' }}>{renderProviderSection('tvdb')}</div>
        <div style={{ flex: 1, minWidth: '320px' }}>{renderProviderSection('mal')}</div>
      </div>
    </section>
  );
}
