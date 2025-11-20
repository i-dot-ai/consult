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

// Shared fetch logic
export const createFetchStore = (mockFetch?: Function) => {
  const store: Writable<{
    data: any,
    isLoading: boolean,
    error: string,
    status: number,
    fetch: Function,
  }> = writable({
    data: null,
    isLoading: false,
    error: "",
    status: 0,
    fetch: () => {},
  });

  const DEBOUNCE_DELAY = 500;
  let debounceTimeout: ReturnType<typeof setTimeout> | null = null;
  let prevPromise: Promise<void> | null = null;
  let resolvePrev: (() => void) | null = null;

  const doFetch = async (
    url: string,
    method: string = "GET",
    body?: BodyInit,
    headers?: HeadersInit,
  ) => {
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
      debounceTimeout = null;
    } else {
      store.update(store => ({...store, isLoading: true, error: ""}));
    }

    prevPromise = new Promise<void>((resolve) => {
      resolvePrev = resolve;

      debounceTimeout = setTimeout(async () => {
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

            store.update(store => ({...store, data: mockData }));
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
              store.update(store => ({...store, data: parsedData}));
            }
            store.update(store => ({...store, status: response.status}));

            if (!response.ok) {
              throw new Error(`Fetch Error: ${response.statusText}`);
            }
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "unknown";
          store.update(store => ({...store, error: message}));
        } finally {
          store.update(store => ({...store, isLoading: false}));
          if (resolvePrev) {
            resolvePrev();
          }
        }
      }, DEBOUNCE_DELAY);
    });

    return prevPromise;
  };

  store.update(store => ({ ...store, fetch: doFetch }))
  return store;
};
