import { Anime, Episode, Stats } from './types';

export async function getStats(): Promise<Stats> {
  const res = await fetch('/api/stats');
  return res.json();
}

export async function getQueue(filter = 'ALL', status = 'ALL', format = 'ALL', offset = 0, sort = 'POPULARITY_DESC', search = ''): Promise<{queue: Anime[], stats: Stats}> {
  const searchParam = search ? `&search_query=${encodeURIComponent(search)}` : '';
  const res = await fetch(`/api/queue?filter=${filter}&status=${status}&format=${format}&offset=${offset}&sort=${sort}&limit=30${searchParam}`);
  return res.json();
}

export async function getAnime(id: number): Promise<Anime> {
  const res = await fetch(`/api/anime/${id}`);
  return res.json();
}

export async function syncEpisodes(anilistId: number, mappings: any[]): Promise<{anilist_id: number, total_episodes: number, episodes: {tmdb: Episode[], tvdb: Episode[]}, mal_fillers?: Record<string, string>}> {
  const res = await fetch(`/api/episodes/sync/${anilistId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mappings })
  });
  return res.json();
}

export async function getPosterPreview(provider: string, id: string, isMovie: boolean = false): Promise<{poster: string, title?: string, date?: string}> {
  const res = await fetch(`/api/poster/${provider}/${id}?movie=${isMovie ? '1' : '0'}`);
  return res.json();
}

export async function verifyAnime(data: any): Promise<any> {
  const res = await fetch('/api/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function unverifyAnime(id: number): Promise<any> {
  const res = await fetch(`/api/unverify/${id}`, { method: 'POST' });
  return res.json();
}

export async function skipAnime(id: number, reason: string): Promise<any> {
  const res = await fetch(`/api/skip/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason })
  });
  return res.json();
}

export async function autoMapAnime(id: number): Promise<{tmdb: {id: string, type: 'show'|'movie'}|null, tvdb: {id: string, type: 'show'|'movie'}|null}> {
  const res = await fetch(`/api/auto_map/${id}`, { method: 'POST' });
  return res.json();
}
