/**
 * Normalizes a title string for fuzzy comparison.
 * Converts to lowercase and strips all non-alphanumeric characters (except spaces,
 * which are kept for word-level tokenization).
 */
function normalizeTitle(s: string): string {
  return (s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '');
}

/**
 * Extracts all numeric substrings from a title and concatenates them.
 * Used as a "number guard" to prevent e.g. "Episode 1" from matching "Episode 2".
 */
function extractNumbers(s: string): string {
  return s.match(/\d+/g)?.join('') || '';
}

/**
 * Creates a simple term frequency vector (bag of words) for a given text.
 */
function getWordVector(text: string): Record<string, number> {
  const words = text.split(/\s+/).filter(w => w.length > 0);
  const vector: Record<string, number> = {};
  for (const word of words) {
    vector[word] = (vector[word] || 0) + 1;
  }
  return vector;
}

/**
 * Calculates the cosine similarity between two term frequency vectors.
 * Returns a value between 0 (no similarity) and 1 (identical).
 */
function cosineSimilarity(vec1: Record<string, number>, vec2: Record<string, number>): number {
  const intersection = Object.keys(vec1).filter(key => vec2.hasOwnProperty(key));
  
  let dotProduct = 0;
  for (const key of intersection) {
    dotProduct += vec1[key] * vec2[key];
  }
  
  let mag1 = 0;
  for (const key in vec1) {
    mag1 += vec1[key] * vec1[key];
  }
  
  let mag2 = 0;
  for (const key in vec2) {
    mag2 += vec2[key] * vec2[key];
  }
  
  if (mag1 === 0 || mag2 === 0) return 0;
  
  return dotProduct / (Math.sqrt(mag1) * Math.sqrt(mag2));
}

/**
 * Determines whether two episode titles are considered a match.
 *
 * Strategy:
 *  1. Fast path: exact match after normalization.
 *  2. Number guard: numbers extracted from both original titles must be identical.
 *  3. Vector-based similarity: Computes cosine similarity of word frequencies.
 *     This is extremely lightweight math (no neural networks) that still handles
 *     word-order differences (e.g., "Pirate King" vs "King of the Pirates").
 *
 * @param t1 - First title string (e.g. TMDB episode name)
 * @param t2 - Second title string (e.g. TVDB episode name)
 * @returns true if the titles are considered a match
 */
export function titlesMatch(t1: string, t2: string): boolean {
  const s1 = normalizeTitle(t1);
  const s2 = normalizeTitle(t2);

  // Empty strings never match
  if (s1.trim().length === 0 || s2.trim().length === 0) return false;

  // Fast path: exact match after normalization
  if (s1 === s2) return true;

  // Number guard: both titles must contain the same digit sequences
  const num1 = extractNumbers(t1);
  const num2 = extractNumbers(t2);
  if (num1 !== num2) return false;

  // Simple Word Vector match using Cosine Similarity (threshold: 70%)
  const vec1 = getWordVector(s1);
  const vec2 = getWordVector(s2);
  
  const similarity = cosineSimilarity(vec1, vec2);
  return similarity >= 0.7; // 70% threshold is generally good for short titles
}


