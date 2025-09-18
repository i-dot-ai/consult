function createThemeFiltersState() {
    const MAX_THEME_FILTERS = Infinity;

    let themeFilters: string[] = $state([]);

    return {
        get filters() { return themeFilters },

        applied: () => {
            return themeFilters.length > 0;
        },

        reset: () => {
            themeFilters = [];
        },

        update: (newFilter: string) => {
            if (!newFilter) {
                // Clear filters if newFilter is falsy
                themeFilters = [];
                return;
            }
            if (themeFilters.includes(newFilter)) {
                themeFilters = [...themeFilters.filter(filter => filter !== newFilter)];
            } else {
                if (themeFilters.length === MAX_THEME_FILTERS) {
                    themeFilters = [...themeFilters.slice(1), newFilter];
                } else {
                    themeFilters = [...themeFilters, newFilter];
                }
            }
        }
    }
}
export const themeFilters = createThemeFiltersState();


function createDemoFiltersState() {
    let demoFilters: {[key: string]: string[]} = $state({});

    return {
        get filters() { return demoFilters },

        reset: () => {
            demoFilters = {};
        },

        applied: (): boolean => {
            for (const key of Object.keys(demoFilters)) {
                const filterArr = demoFilters[key];

                // filterArr can be undefined or empty array
                if (filterArr && filterArr.filter(Boolean).length > 0) {
                    return true;
                }
            }
            return false;
        },

        update: (newFilterKey: string, newFilterValue: string) => {
            if (!newFilterKey || !newFilterValue) {
                // Clear filters if nothing is passed
                demoFilters = {};
                return;
            }

            const existingFilters = demoFilters[newFilterKey] || [];

            let resultFilters;
            if (existingFilters.includes(newFilterValue)) {
                // Remove filter if already added
                resultFilters = existingFilters.filter(filter => newFilterValue !== filter);
            } else {
                // Avoid duplicates when adding filters
                resultFilters = [...new Set([...existingFilters, newFilterValue])];
            }

            demoFilters = {
                ...demoFilters,
                [newFilterKey]: resultFilters,
            }
        }
    }
}
export const demoFilters = createDemoFiltersState();


function createMultiAnswerFiltersState() {
    let multiAnswerFilters: string[] = $state([]);

    return {
        get filters() { return multiAnswerFilters },

        reset: () => {
            multiAnswerFilters = [];
        },

        applied: (answer?: string): boolean => {
            // if no answer specified, return true if any applied
            if (!answer) {
                return multiAnswerFilters.length > 0;
            }
            // if answer specified, return true if it's applied
            return multiAnswerFilters.includes(answer);
        },

        update: (newFilter?: string) => {
            if (!newFilter) {
                return;
            }
            if (multiAnswerFilters.includes(newFilter)) {
                multiAnswerFilters = multiAnswerFilters.filter(filter => filter != newFilter);
            } else {
                multiAnswerFilters = [...multiAnswerFilters, newFilter];
            }
        }
    }
}
export const multiAnswerFilters = createMultiAnswerFiltersState();