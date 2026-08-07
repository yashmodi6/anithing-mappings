export interface Stats {
  total_count: number;
  verified_count: number;
  percentage?: number;
}

export interface Mapping {
  provider: 'tmdb' | 'tvdb' | 'mal' | 'imdb';
  type: 'show' | 'movie';
  id: string | number;
  scope?: string;
  episode_mapping?: string;
  episodes?: Record<string, string>;
  _preview?: any;
  _dirty?: boolean;
}

export interface Anime {
  anilist_id: number;
  title?: string;
  title_english?: string;
  title_romaji?: string;
  format: string;
  status: string;
  is_verified: boolean;
  is_skipped?: boolean;
  episodes?: number;
  released_episodes?: number;
  anilist_poster?: string;
  mappings: Mapping[];
  episode_types: Record<string, string>;
}

export interface Episode {
  season?: string | number;
  episode?: string | number;
  episode_in_season?: string | number;
  thumbnail?: string;
  title?: string;
  name?: string;
  names?: string[];
}

export interface EpisodesMap {
  tmdb: Episode[];
  tvdb: Episode[];
}
