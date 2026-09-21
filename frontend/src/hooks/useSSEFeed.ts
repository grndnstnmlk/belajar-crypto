import { useEffect, useState } from 'react';
import { fetchFeed } from '../services/api';
import type { FeedData } from '../types/market';

export function useSSEFeed() {
  const [feed, setFeed] = useState<FeedData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isFallback, setIsFallback] = useState(false);

  useEffect(() => {
    let sseSource: EventSource | null = null;
    let pollInterval: any = null;

    const startPolling = () => {
      setIsFallback(true);
      if (!pollInterval) {
        pollInterval = setInterval(async () => {
          try {
            const data = await fetchFeed();
            setFeed(data);
            setIsConnected(true);
          } catch {
            setIsConnected(false);
          }
        }, 2000);
      }
    };

    if (!window.EventSource) {
      startPolling();
      return;
    }

    try {
      sseSource = new EventSource('/api/stream/events');

      sseSource.onopen = () => {
        setIsConnected(true);
        setIsFallback(false);
        if (pollInterval) {
          clearInterval(pollInterval);
          pollInterval = null;
        }
      };

      sseSource.onmessage = (event) => {
        try {
          const data: FeedData = JSON.parse(event.data);
          setFeed(data);
          setIsConnected(true);
        } catch (e) {
          console.warn('SSE JSON parse error:', e);
        }
      };

      sseSource.onerror = () => {
        setIsConnected(false);
        startPolling();
      };
    } catch {
      startPolling();
    }

    // Initial snapshot fetch
    fetchFeed()
      .then((data) => setFeed(data))
      .catch(() => {});

    return () => {
      if (sseSource) sseSource.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  return { feed, isConnected, isFallback };
}
