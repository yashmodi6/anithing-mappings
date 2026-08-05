import { Anime, Episode, Stats } from './types';

export async function getStats(): Promise<Stats> {
  const res = await fetch('/api/stats');
  return res.json();
}

export async function getQueue(filter = 'ALL', status = 'ALL', format = 'ALL', offset = 0, sort = 'POPULARITY_DESC'): Promise<{queue: Anime[], stats: Stats}> {
  const res = await fetch(`/api/queue?filter=${filter}&status=${status}&format=${format}&offset=${offset}&sort=${sort}&limit=30`);
  return res.json();
}

export async function getAnime(id: number): Promise<Anime> {
  const res = await fetch(`/api/anime/${id}`);
  return res.json();
}

export async function getEpisodes(provider: string, anilistId: number, mappings = null, overrideId: string | null = null): Promise<{anilist_id: number, total_episodes: number, episodes: Episode[]}> {
  const body: any = {};
  if (mappings) body.mappings = mappings;
  if (overrideId) body[`${provider}_id`] = overrideId;
  
  const options = Object.keys(body).length > 0 ? {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  } : {};
  const res = await fetch(`/api/episodes/${provider}/${anilistId}`, options);
  return res.json();
}

export async function getPosterPreview(provider: string, id: string, isMovie: boolean = false): Promise<{poster: string}> {
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


