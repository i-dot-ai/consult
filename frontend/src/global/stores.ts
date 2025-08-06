import { writable } from "svelte/store";

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