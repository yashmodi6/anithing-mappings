export interface CompressibleEpisode {
  global_episode: number;
  season?: number;
  episode_in_season?: number;
}

/**
 * Compresses an array of episodes into a JSON mapping string.
 * Example: [{"global_episode": 1, "season": 1, "episode_in_season": 1}] -> '{"s1":{"1":"1"}}'
 */
export function compressEpisodesToJSON(episodes: CompressibleEpisode[]): string {
  const result: Record<string, Record<string, string>> = {};
  
  // Group by season
  const bySeason: Record<string, CompressibleEpisode[]> = {};
  for (const ep of episodes) {
    if (ep.season == null || ep.episode_in_season == null) continue;
    const s = `s${ep.season}`;
    if (!bySeason[s]) bySeason[s] = [];
    bySeason[s].push(ep);
  }
  
  for (const [season, eps] of Object.entries(bySeason)) {
    // Sort by global_episode to ensure contiguous detection works
    eps.sort((a, b) => a.global_episode - b.global_episode);
    
    result[season] = {};
    if (eps.length === 0) continue;
    
    let startEp = eps[0];
    let prevEp = eps[0];
    
    for (let i = 1; i < eps.length; i++) {
      const curr = eps[i];
      // Check if contiguous
      if (
        curr.global_episode === prevEp.global_episode + 1 &&
        curr.episode_in_season! === prevEp.episode_in_season! + 1
      ) {
        prevEp = curr;
      } else {
        // End of sequence
        const globalRange = startEp.global_episode === prevEp.global_episode ? 
                            `${startEp.global_episode}` : 
                            `${startEp.global_episode}-${prevEp.global_episode}`;
                            
        const localRange = startEp.episode_in_season === prevEp.episode_in_season ? 
                           `${startEp.episode_in_season}` : 
                           `${startEp.episode_in_season}-${prevEp.episode_in_season}`;
                           
        result[season][globalRange] = localRange;
        
        startEp = curr;
        prevEp = curr;
      }
    }
    
    // Add final sequence
    const globalRange = startEp.global_episode === prevEp.global_episode ? 
                        `${startEp.global_episode}` : 
                        `${startEp.global_episode}-${prevEp.global_episode}`;
                        
    const localRange = startEp.episode_in_season === prevEp.episode_in_season ? 
                       `${startEp.episode_in_season}` : 
                       `${startEp.episode_in_season}-${prevEp.episode_in_season}`;
                       
    result[season][globalRange] = localRange;
  }
  
  return JSON.stringify(result);
}

export interface ExpandedLookup {
  [globalEpisode: number]: { season: number; episode_in_season: number };
}

/**
 * Expands a JSON mapping string into a dictionary of global_episode -> {season, episode_in_season}
 */
export function expandJSONToEpisodes(jsonString: string): ExpandedLookup {
  const lookup: ExpandedLookup = {};
  if (!jsonString) return lookup;
  
  try {
    const mapping = JSON.parse(jsonString);
    if (typeof mapping !== 'object') return lookup;
    
    for (const seasonKey of Object.keys(mapping)) {
      if (!seasonKey.startsWith('s')) continue;
      const sNum = parseInt(seasonKey.replace('s', ''), 10);
      if (isNaN(sNum)) continue;
      
      const ranges = mapping[seasonKey];
      for (const globalRange of Object.keys(ranges)) {
        const localRange = ranges[globalRange];
        
        const gParts = String(globalRange).split('-');
        const gStart = parseInt(gParts[0], 10);
        let gEnd = gParts.length > 1 && gParts[1] ? parseInt(gParts[1], 10) : gStart;
        if (gParts.length > 1 && !gParts[1]) gEnd = gStart + 2000;
        
        const lParts = String(localRange).split('-');
        const lStart = parseInt(lParts[0], 10);
        
        let gIdx = gStart;
        let lIdx = lStart;
        
        while (gIdx <= gEnd && (gIdx - gStart) < 2000) {
          lookup[gIdx] = { season: sNum, episode_in_season: lIdx };
          gIdx++;
          lIdx++;
        }
      }
    }
  } catch (e) {
    console.error("Error expanding JSON:", e);
  }
  return lookup;
}
