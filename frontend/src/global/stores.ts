import { writable } from "svelte/store";


// Favourite questions logic
const FAVS_STORAGE_KEY = "favouritedQuestions";
function getInitialFavs() {
    if (typeof localStorage === "undefined") {
        return []
    };
    
    const storedFavs = localStorage.getItem(FAVS_STORAGE_KEY);
    try {
        return storedFavs ? JSON.parse(storedFavs) : [];
    } catch(e) {
        return [];
    }
}

function createFavStore() {
    const { subscribe, set, update } = writable(getInitialFavs());

    const syncLocalStorage = (val: Array<string>) => {
        localStorage.setItem(FAVS_STORAGE_KEY, JSON.stringify(val));
    }

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
            })
        },
    }
}
export const favStore = createFavStore();


// Shared fetch logic
export const createFetchStore = () => {
    const data = writable(null);
    const loading = writable(true);
    const error = writable(null);

    const DEBOUNCE_DELAY = 500;
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null;
    let prevPromise: Promise<void> | null = null;
    let resolvePrev: (() => void) | null = null;

    const load = async (url: string, method:string="GET", body?: BodyInit) => {
        if (debounceTimeout) {
            clearTimeout(debounceTimeout);
            debounceTimeout = null;
        }

        prevPromise = new Promise<void>((resolve) => {
            resolvePrev = resolve;

            debounceTimeout = setTimeout(async () => {
                loading.set(true);
                error.set(null);
                try {
                    const response = await fetch(
                        url,
                        {
                            method: method,
                            body: body ? JSON.stringify(body) : undefined,
                        }
                    );
                    if (!response.ok) {
                        throw new Error(`Fetch Error: ${response.statusText}`);
                    }
                    const parsedData = await response.json();
                    data.set(parsedData);
                } catch(err: any) {
                    error.set(err.message);
                } finally {
                    loading.set(false);

                    if (resolvePrev) {
                        resolvePrev();
                    }
                }
            }, DEBOUNCE_DELAY);
        })

        return prevPromise;
    };

    return { data, loading, error, load };
}