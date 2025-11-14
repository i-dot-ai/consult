import { writable } from "svelte/store";
import type { Writable } from "svelte/store";

// Favourite questions logic
const FAVS_STORAGE_KEY = "favouritedQuestions";
function getInitialFavs() {
  if (typeof localStorage === "undefined") {
    return [];
  }

  const storedFavs = localStorage.getItem(FAVS_STORAGE_KEY);
  try {
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

export type MockFetch = (requestInfo: {
  url: string;
  headers?: HeadersInit;
  method: string;
  body?: string;
}) => unknown;

// Shared fetch logic
export const createFetchStore = (mockFetch?: MockFetch) => {
  const data: Writable<unknown> = writable(null);
  const loading: Writable<boolean> = writable(true);
  const error: Writable<string> = writable("");

  const DEBOUNCE_DELAY = 500;
  let debounceTimeout: ReturnType<typeof setTimeout> | null = null;
  let prevPromise: Promise<void> | null = null;
  let resolvePrev: (() => void) | null = null;

  const load = async (
    url: string,
    method: string = "GET",
    body?: BodyInit,
    headers?: HeadersInit,
  ) => {
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
      debounceTimeout = null;
    }

    prevPromise = new Promise<void>((resolve) => {
      resolvePrev = resolve;

      debounceTimeout = setTimeout(async () => {
        loading.set(true);
        error.set("");
        try {
          if (mockFetch) {
            data.set(
              mockFetch({
                url: url,
                headers: {
                  "Content-Type": "application/json",
                  ...headers,
                },
                method: method,
                body: body ? JSON.stringify(body) : undefined,
              }),
            );
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
            const parsedData = await response.json();
            data.set(parsedData);
            if (!response.ok) {
              throw new Error(`Fetch Error: ${response.statusText}`);
            }
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "unknown";
          error.set(message);
        } finally {
          loading.set(false);
          if (resolvePrev) {
            resolvePrev();
          }
        }
      }, DEBOUNCE_DELAY);
    });

    return prevPromise;
  };

  return { data, loading, error, load };
};
