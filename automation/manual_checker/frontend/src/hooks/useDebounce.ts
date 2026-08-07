import { useEffect, useRef, useState } from 'react';

/**
 * Returns a debounced version of the given value.
 * The returned value only updates after the user has stopped changing it
 * for `delayMs` milliseconds.
 *
 * @param value - The value to debounce
 * @param delayMs - Delay in milliseconds (default: 300ms)
 */
export function useDebounce<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

/**
 * Returns a stable debounced callback function.
 * The callback fires only after `delayMs` ms have passed since the last call.
 *
 * @param fn - The function to debounce
 * @param delayMs - Delay in milliseconds (default: 300ms)
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  fn: T,
  delayMs = 300
): T {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  return ((...args: Parameters<T>) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), delayMs);
  }) as T;
}
