import { useQuery } from '@tanstack/react-query';

import { api, type Health } from './client';

/** Polls the backend health endpoint. UI components never call `fetch` directly. */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async (): Promise<Health> => {
      const { data, error } = await api.GET('/api/health');
      if (error !== undefined || data === undefined) {
        throw new Error('API health check failed');
      }
      return data;
    },
    refetchInterval: 10_000,
    retry: false,
  });
}
