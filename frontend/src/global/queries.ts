import { QueryClient, createQuery } from "@tanstack/svelte-query";

export const queryClient = new QueryClient();

interface Options {
  key: string[],
  errorMessage?: string,
}

export const buildQuery = <T>(url: string, options: Options) => {
  return createQuery<T>(() => ({
      queryKey: options.key,
      queryFn: async () => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(options.errorMessage || "Query failed");
        return await response.json();
      },
    }),
    () => queryClient,
  );
}
