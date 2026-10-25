"use client";

import { useEffect, useEffectEvent, useState } from "react";

interface Settled<T> {
  tick: number;
  key: string;
  data?: T;
  error?: unknown;
}

/**
 * Load one async resource for a key, with retry. Loading is derived (no setState in the effect body),
 * so it satisfies the React compiler rules and never shows stale data for a new key.
 */
export function useResource<T>(fetcher: () => Promise<T>, key: string) {
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const run = useEffectEvent(fetcher);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await run();
        if (!cancelled) setSettled({ tick, key, data });
      } catch (error) {
        if (!cancelled) setSettled({ tick, key, error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tick, key]);

  const current = settled && settled.tick === tick && settled.key === key ? settled : null;
  return {
    loading: current === null,
    data: current?.data,
    error: current?.error,
    reload: () => setTick((t) => t + 1),
  };
}
