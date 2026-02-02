import { writable } from "svelte/store";
import type { Writable } from "svelte/store";

import { debounce } from "./utils";

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
