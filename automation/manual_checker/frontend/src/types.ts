export interface Stats {
  total_count: number;
  verified_count: number;
  percentage?: number;
}

export interface Anime {
  anilist_id: number;
  title?: string;
  title_english?: string;
  title_romaji?: string;
  format: string;
  status: string;
  is_verified: boolean;
  episodes?: number;
  released_episodes?: number;
  tmdb_show_id?: string;
  tmdb_movie_id?: string;
  tvdb_show_id?: string;
  tvdb_movie_id?: string;
  mal_id?: string;
  anilist_poster?: string;
  tmdb_poster?: string;
  tmdb_title?: string;
  tmdb_date?: string;
  tvdb_poster?: string;
  tvdb_title?: string;
  tvdb_date?: string;
  mal_poster?: string;
  mal_title?: string;
  mal_date?: string;
}

export interface Episode {
  season?: string | number;
  episode?: string | number;
  thumbnail?: string;
  title?: string;
  names?: string[];
}

export interface EpisodesMap {
  tmdb: Episode[];
  tvdb: Episode[];
}

export interface Provider {
  id: string;
  name: string;
  logo?: string;
  currentId: string;
  poster?: string;
  title?: string;
  date?: string;
}
