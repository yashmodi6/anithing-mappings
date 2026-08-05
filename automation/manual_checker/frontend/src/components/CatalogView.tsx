import React from 'react';
import { Search } from 'lucide-react';
import { Anime } from '../types';

interface CatalogViewProps {
  catalog: Anime[];
  searchQ: string;
  setSearchQ: (q: string) => void;
  filter: string;
  setFilter: (f: string) => void;
  status: string;
  setStatus: (s: string) => void;
  format: string;
  setFormat: (f: string) => void;
  sort: string;
  setSort: (s: string) => void;
  loadCatalog: () => void;
  loadMore: () => void;
  handleAnimeClick: (id: number) => void;
}

export default function CatalogView({ 
  catalog, searchQ, setSearchQ, filter, setFilter, 
  status, setStatus, format, setFormat, sort, setSort, loadCatalog, loadMore, handleAnimeClick 
}: CatalogViewProps) {
  return (
    <div className="flex-col gap-md animate-in">
      <div className="flex-row justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Catalog</h2>
      </div>

      <div className="card flex-row gap-md items-center" style={{ flexWrap: 'wrap' }}>
        <div className="flex-row items-center gap-sm input-field" style={{ flex: '1 1 300px' }}>
          <Search size={16} className="text-muted" />
          <input 
            type="text" placeholder="Search catalog..." 
            style={{ background: 'transparent', border: 'none', color: 'inherit', outline: 'none', width: '100%' }} 
            value={searchQ} onChange={e => setSearchQ(e.target.value)} 
            onBlur={loadCatalog} onKeyDown={e => e.key === 'Enter' && loadCatalog()} 
          />
        </div>

        <select className="input-field" style={{ width: 'auto', appearance: 'auto', backgroundColor: 'var(--surface)' }} value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="ALL">All Entries</option>
          <option value="VERIFIED">Verified</option>
          <option value="UNVERIFIED">Unverified</option>
        </select>

        <select className="input-field" style={{ width: 'auto', appearance: 'auto', backgroundColor: 'var(--surface)' }} value={status} onChange={e => setStatus(e.target.value)}>
          <option value="ALL">All Statuses</option>
          <option value="FINISHED">Finished Airing</option>
          <option value="RELEASING">Currently Airing</option>
          <option value="NOT_YET_RELEASED">Not Yet Aired</option>
        </select>

        <select className="input-field" style={{ width: 'auto', appearance: 'auto', backgroundColor: 'var(--surface)' }} value={format} onChange={e => setFormat(e.target.value)}>
          <option value="ALL">All Formats</option>
          <option value="TV">TV</option>
          <option value="MOVIE">Movie</option>
          <option value="OVA">OVA</option>
          <option value="ONA">ONA</option>
        </select>
        
        <select className="input-field" style={{ width: 'auto', appearance: 'auto', backgroundColor: 'var(--surface)' }} value={sort} onChange={e => setSort(e.target.value)}>
          <option value="POPULARITY_DESC">Sort: Most Popular</option>
          <option value="ID_ASC">Sort: Oldest First (ID Asc)</option>
          <option value="ID_DESC">Sort: Newest First (ID Desc)</option>
        </select>
      </div>

      <div className="provider-grid mt-4">
        {catalog.map(anime => (
          <div key={anime.anilist_id} className="card flex-col justify-center" style={{ padding: '16px', cursor: 'pointer' }} onClick={() => handleAnimeClick(anime.anilist_id)}>
            <span className="font-bold text-base truncate mb-2">{anime.title || anime.title_english || anime.title_romaji}</span>
            <div className="flex-row justify-between text-xs text-muted">
              <span>{anime.format} • {anime.status}</span>
              {anime.is_verified ? <span className="text-success font-medium">Verified</span> : <span className="text-warning font-medium">Unverified</span>}
            </div>
          </div>
        ))}
        {catalog.length === 0 && <div className="text-muted">No anime found in this filter.</div>}
      </div>
      {catalog.length > 0 && (
        <div className="flex-row justify-center mt-4">
          <button className="btn btn-secondary" onClick={loadMore}>
            Load More
          </button>
        </div>
      )}
    </div>
  );
}
