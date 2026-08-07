import React from 'react';
import { Stats } from '../../types';

interface HeaderProps {
  currentView: string;
  setCurrentView: (view: string) => void;
  stats: Stats;
}

export default function Header({ currentView, setCurrentView, stats }: HeaderProps) {
  const handleComplete = async () => {
    try {
      const res = await fetch('/api/shutdown', { method: 'POST' });
      const data = await res.json();
      if (data.success) alert(data.message);
    } catch (e) {
      alert('Failed to shut down server.');
    }
  };

  return (
    <header className="header-glass flex-row justify-between items-center">
      <div className="flex-row items-center gap-md">
        <h1 className="text-xl font-bold text-accent">Anithing</h1>
        <div className="flex-row gap-sm text-sm font-medium" style={{ marginLeft: '16px' }}>
          <button className="btn" style={{ padding: 0, background: 'none', color: currentView === 'home' ? 'var(--accent)' : 'var(--text-muted)' }} onClick={() => setCurrentView('home')}>Home</button>
          <span className="text-muted">|</span>
          <button className="btn" style={{ padding: 0, background: 'none', color: currentView === 'catalog' ? 'var(--accent)' : 'var(--text-muted)' }} onClick={() => setCurrentView('catalog')}>Catalog</button>
        </div>
      </div>
      <div className="flex-row items-center gap-md text-sm">
        <span className="text-muted">Total Anime: <span className="text-primary font-bold">{stats.total_count}</span></span>
        <span className="text-muted">Total Verified: <span className="text-success font-bold">{stats.verified_count}</span></span>
      </div>
      <div className="flex-row gap-sm items-center">
        <select 
          className="select select-sm" 
          onChange={(e) => { if(e.target.value) window.open(e.target.value, '_blank'); e.target.value=''; }}
          style={{ padding: '6px 12px', fontSize: '13px', background: 'var(--surface)', color: 'var(--text-main)', border: '1px solid var(--border)', borderRadius: '6px', cursor: 'pointer' }}
        >
          <option value="">View JSONs...</option>
          <option value="/api/mapping-tv.json">mapping-tv.json</option>
          <option value="/api/mapping-movie.json">mapping-movie.json</option>
          <option value="/api/mapping-special.json">mapping-special.json</option>
          <option value="/api/mapping-ova.json">mapping-ova.json</option>
          <option value="/api/mapping-ona.json">mapping-ona.json</option>
          <option value="/api/skipped.json">skipped-anime.json</option>
        </select>
        <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '13px' }} onClick={handleComplete}>
          Complete for now
        </button>
      </div>
    </header>
  );
}
