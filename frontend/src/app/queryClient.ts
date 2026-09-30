import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes fresh
      gcTime: 1000 * 60 * 15, // 15 minutes garbage collection
      retry: 1,
      refetchOnWindowFocus: true, // auto-refetch on tab refocus for live telemetry
    },
  },
});
