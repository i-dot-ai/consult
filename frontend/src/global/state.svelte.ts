function createThemeFiltersState() {
    const MAX_THEME_FILTERS = Infinity;

    let themeFilters = $state([]);

    return {
        get filters() { return themeFilters },

        applied: () => {
            return themeFilters.length > 0;
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