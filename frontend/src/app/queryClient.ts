import { QueryClient } from '@tanstack/react-query'

/**
 * Single QueryClient for the app.
 * staleTime is generous because curriculum content is effectively static;
 * progress reads are invalidated explicitly after a session submit.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
