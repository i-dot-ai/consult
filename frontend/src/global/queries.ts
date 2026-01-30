import { QueryClient, createMutation, createQuery } from "@tanstack/svelte-query";
import { type HttpMethod } from "../global/types";

import { persistQueryClient } from '@tanstack/svelte-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 1,
      refetchOnMount: false,
      refetchOnWindowFocus: false,
    }
  }
});

interface BuildQueryOptions {
  key?: string[],
  errorMessage?: string,
  method?: HttpMethod,
  headers?: HeadersInit,
  onSuccess?: () => Promise<void>,
}

interface MutationArgs {
  body?: BodyInit,
  headers?: HeadersInit,
  params?: { string: string },
}

const doFetch = async (
  url: string,
  method: BuildQueryOptions["method"],
  errorMessage: BuildQueryOptions["errorMessage"],
  body?: BodyInit,
  headers?: HeadersInit,
) => {
  const response = await fetch(url, {
    method: method,
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json",
      ...headers,
    }
  });
  if (!response.ok) throw new Error(errorMessage);
  return await response.json();
}

const applyParams = (url: string, params: MutationArgs["params"]): string => {
  let result = url.slice(0);

  Object.keys(params!).forEach(key => {
    result = result.replaceAll(`:${key}`, params[key]);
  })

  return result;
}

export const buildQuery = <T>(url: string, {
  key,
  errorMessage = "Query failed",
  method = "GET",
  headers,
  onSuccess,
}: BuildQueryOptions) => {
  // Create mutation for mutating methods
  if ((["POST", "PUT", "PATCH", "DELETE"] as HttpMethod[]).includes(method)) {
    return createMutation(() => ({
      queryKey: key,
      mutationFn: async ({ body, params }: MutationArgs) => {
        const finalUrl = params ? applyParams(url, params) : url;
        return await doFetch(finalUrl, method, errorMessage, body!);
      },
      onSuccess: onSuccess,
    }),
    () => queryClient
  )}

  // Create query for non-mutating methods
  return createQuery<T>(() => ({
      queryKey: key!,
      queryFn: () => doFetch(url, method, errorMessage, undefined, headers),
      onSuccess: onSuccess,
    }),
    () => queryClient,
  );
}

persistQueryClient({
  queryClient,
  persister: createSyncStoragePersister({
    storage: window.localStorage,
  })
})