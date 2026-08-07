import * as fuzz from 'fuzzball';

/**
 * Normalizes a title string for fuzzy comparison.
 * Converts to lowercase and strips all non-alphanumeric characters (except spaces,
 * which are kept for word-level tokenization in fuzzball).
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
 * Determines whether two episode titles are considered a match.
 *
 * Strategy:
 *  1. Fast path: exact match after normalization.
 *  2. Number guard: numbers extracted from both original titles must be identical.
 *     This prevents "Episode 1" from fuzzy-matching "Episode 2".
 *  3. Fuzzy match: fuzzball token_sort_ratio >= 80 (0-100 scale).
 *     token_sort_ratio sorts words alphabetically before comparing, which handles
 *     word-order differences caused by translation (e.g. "Pirate King" vs "King of the Pirates").
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

  // Fuzzy match using token_sort_ratio (threshold: 80%)
  const score = fuzz.token_sort_ratio(s1, s2);
  return score >= 80;
}
