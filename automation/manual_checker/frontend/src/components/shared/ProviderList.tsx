import React from 'react';
import { Search, Loader2, RotateCcw } from 'lucide-react';
import { Provider } from '../../types';

interface ProviderListProps {
  provs: Provider[];
  providerChanges: Record<string, boolean>;
  savingProviders: Record<string, boolean>;
  animeTitle: string;
  providerTypes?: Record<string, 'show' | 'movie'>;
  isAutoMapping?: boolean;
  handleProviderIdChange: (id: string, val: string) => void;
  handleProviderTypeChange?: (id: string, val: 'show' | 'movie') => void;
  handleProviderSave: (id: string) => void;
  handleAutoMap?: () => void;
  handleReset?: () => void;
}

export default function ProviderList({ provs, providerChanges, savingProviders, animeTitle, providerTypes, isAutoMapping, handleProviderIdChange, handleProviderTypeChange, handleProviderSave, handleAutoMap, handleReset }: ProviderListProps) {
  const handleSearch = (providerId: string) => {
    const q = encodeURIComponent(animeTitle);
    let url = '';
    switch (providerId) {
      case 'mal': url = `https://myanimelist.net/anime.php?q=${q}&cat=anime`; break;
      case 'tmdb': url = `https://www.themoviedb.org/search?query=${q}`; break;
      case 'tvdb': url = `https://thetvdb.com/search?query=${q}`; break;
      case 'anilist': url = `https://anilist.co/search/anime?search=${q}`; break;
    }
    if (url) window.open(url, '_blank');
  };

  return (
    <section className="flex-col gap-md animate-in" style={{ animationDelay: '0.1s' }}>
      <div className="flex-row justify-between items-center">
        <h3 className="text-xl">Provider ID Mapping</h3>
        <div className="flex-row gap-sm">
          {handleReset && (
            <button 
              className="btn btn-outline btn-sm flex-row gap-sm items-center text-muted" 
              onClick={handleReset}
              title="Reset all fields to database defaults"
            >
              <RotateCcw size={14} />
              Reset
            </button>
          )}
          {handleAutoMap && (
            <button 
              className="btn btn-outline btn-sm flex-row gap-sm items-center" 
              onClick={handleAutoMap}
              disabled={isAutoMapping}
            >
              {isAutoMapping && <Loader2 className="animate-spin" size={14} />}
              Auto Map
            </button>
          )}
        </div>
      </div>
      <div className="provider-grid">
        {provs.map(p => (
          <div key={p.id} className="card flex-col gap-md">
            <div className="flex-row justify-between">
              <div className="flex-row gap-sm font-semibold">
                <div className="badge badge-neutral">{p.logo}</div>
                {p.name}
              </div>
              <div className="flex-row gap-sm">
                <button className="btn-icon" title="Search" onClick={() => handleSearch(p.id)}><Search size={18} /></button>
              </div>
            </div>
            
            {p.poster ? (
              <img src={p.poster} alt={`${p.name} poster`} className="provider-poster" />
            ) : (
              <div className="provider-poster flex-col justify-center items-center text-muted text-xs">No Poster</div>
            )}
            
            <div className="flex-row gap-sm items-center">
              {(p.id === 'tmdb' || p.id === 'tvdb') && providerTypes && handleProviderTypeChange && (
                <select 
                  className="select" 
                  value={providerTypes[p.id] || 'show'} 
                  onChange={(e) => handleProviderTypeChange(p.id, e.target.value as 'show' | 'movie')}
                >
                  <option value="show">TV Show</option>
                  <option value="movie">Movie</option>
                </select>
              )}
              <input 
                type="text" 
                className="input-field" 
                value={p.currentId || ''} 
                onChange={(e) => handleProviderIdChange(p.id, e.target.value)}
                disabled={p.id === 'anilist'}
                style={{ flex: 1 }}
              />
              {p.id !== 'anilist' && (
                <button 
                  className={`btn ${providerChanges[p.id] ? 'btn-primary' : 'btn-outline'}`} 
                  onClick={() => handleProviderSave(p.id)}
                  disabled={!providerChanges[p.id] || savingProviders[p.id]}
                >
                  {savingProviders[p.id] ? <Loader2 className="animate-spin" size={16} /> : 'Save'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
