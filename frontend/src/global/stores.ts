import { writable } from "svelte/store";
import type { Writable } from "svelte/store";

import { debounce, dotEnv } from "./utils";
import {
  Client,
  type EmptyTypes,
  type HttpMethodsType,
} from "@hyper-fetch/core";

// Favourite questions logic
const FAVS_STORAGE_KEY = "favouritedQuestions";
function getInitialFavs() {
  if (typeof localStorage === "undefined") {
    return [];
  }

  try {
    const storedFavs = localStorage.getItem(FAVS_STORAGE_KEY);
    return storedFavs ? JSON.parse(storedFavs) : [];
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (err) {
    return [];
  }
}

function createFavStore() {
  const { subscribe, update } = writable(getInitialFavs());

  const syncLocalStorage = (val: Array<string>) => {
    localStorage.setItem(FAVS_STORAGE_KEY, JSON.stringify(val));
  };

  return {
    subscribe,

    toggleFav: (id: string) => {
      update((ids) => {
        const index = ids.indexOf(id);
        let newIds;

        if (index === -1) {
          newIds = [...ids, id];
        } else {
          newIds = ids.filter((currId: string) => currId !== id);
        }

        syncLocalStorage(newIds);
        return newIds;
      });
    },
  };
}
export const favStore = createFavStore();

export type MockFetch<T> = (config: {
  url: string;
  headers?: HeadersInit;
  method: string;
  body?: string;
}) => T;

// Shared fetch logic
export const createFetchStore = <T>({
  mockFetch,
  debounceDelay = 500,
}: { mockFetch?: MockFetch<T>; debounceDelay?: number } | undefined = {}) => {
  const store: Writable<{
    data: T | null;
    isLoading: boolean;
    error: string | null;
    status: number;
    fetch: (
      url: string,
      method?: string,
      body?: BodyInit,
      headers?: HeadersInit,
    ) => Promise<void>;
  }> = writable({
    data: null,
    isLoading: false,
    error: null,
    status: 0,
    fetch: () => Promise.resolve(),
  });

  let prevPromise: Promise<void> | null = null;
  let resolvePrev: (() => void) | null = null;
  let debouncedFetch: ReturnType<typeof debounce> | null = null;

  const doFetch = async (
    url: string,
    method: string = "GET",
    body?: BodyInit,
    headers?: HeadersInit,
  ) => {
    // immediate feedback to the UI that fetching has started
    // even though it awaits debounce timeout
    store.update((store) => ({ ...store, isLoading: true, error: "" }));

    if (!debouncedFetch) {
      debouncedFetch = debounce(async () => {
        try {
          if (mockFetch) {
            const mockData = mockFetch({
              url: url,
              headers: {
                "Content-Type": "application/json",
                ...headers,
              },
              method: method,
              body: body ? JSON.stringify(body) : undefined,
            });

            store.update((store) => ({ ...store, data: mockData }));
            return;
          } else {
            const response = await fetch(url, {
              headers: {
                "Content-Type": "application/json",
                ...headers,
              },
              method: method,
              body: body ? JSON.stringify(body) : undefined,
            });

            // Avoid error if no body is returned
            // equivalent to .json()
            const textBody = await response.text();
            if (textBody) {
              const parsedData = JSON.parse(textBody);
              store.update((store) => ({ ...store, data: parsedData }));
            }
            store.update((store) => ({ ...store, status: response.status }));

            if (!response.ok) {
              throw new Error(`Fetch Error: ${response.statusText}`);
            }
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "unknown";
          store.update((store) => ({ ...store, error: message }));
        } finally {
          store.update((store) => ({ ...store, isLoading: false }));
          if (resolvePrev) {
            resolvePrev();
          }
        }
      }, debounceDelay);
    }

    prevPromise = new Promise<void>((resolve) => {
      resolvePrev = resolve;

      debouncedFetch!();
    });

    return prevPromise;
  };

  store.update((store) => ({ ...store, fetch: doFetch }));
  return store;
};

interface createQueryStoreOptions {
  method?: HttpMethodsType;
  deduplicate?: boolean;
}
interface createQueryStoreFetchOptions {
  body?: unknown;
  headers?: unknown;
  params?: unknown;
}
export const createQueryStore = <T>(
  url: string,
  options: createQueryStoreOptions | undefined = {
    method: "GET",
    deduplicate: true,
  },
) => {
  const client = new Client({
    url: dotEnv("PUBLIC_FRONTEND_URL"),
  });

  const query = client.createRequest()({
    method: options?.method,
    endpoint: url,
    deduplicate: options?.deduplicate,
  });

  const store: Writable<{
    data: T | undefined;
    isLoading: boolean;
    error: unknown | null;
    status: number | null;
    fetch: (options?: createQueryStoreFetchOptions) => Promise<void>;
    reset: () => void;
  }> = writable({
    data: undefined,
    isLoading: false,
    error: null,
    status: null,
    fetch: async () => {},
    reset: () => {},
  });

  const doFetch = async (
    options: createQueryStoreFetchOptions | undefined = {},
  ) => {
    // set loading to true
    store.update((store) => ({ ...store, isLoading: true }));

    const {
      data: _data,
      error: _error,
      status: _status,
    } = await query
      .setParams(options.params as EmptyTypes)
      .setHeaders(options.headers as HeadersInit)
      .setPayload(options.body as undefined)
      .send();

    // update store
    store.update((store) => ({
      ...store,
      data: _data as T,
      error: _error,
      status: _status,
    }));

    // set loading to false
    store.update((store) => ({ ...store, isLoading: false }));
  };

  const reset = () => {
    store.update((store) => ({
      ...store,
      data: undefined,
      isLoading: false,
      error: null,
      status: null,
    }));
  };
  store.update((store) => ({ ...store, fetch: doFetch, reset: reset }));

  return store;
};
