function createThemeFiltersState() {
  const MAX_THEME_FILTERS = Infinity;

  let themeFilters: string[] = $state([]);

  return {
    get filters() {
      return themeFilters;
    },

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
        themeFilters = [
          ...themeFilters.filter((filter) => filter !== newFilter),
        ];
      } else {
        if (themeFilters.length === MAX_THEME_FILTERS) {
          themeFilters = [...themeFilters.slice(1), newFilter];
        } else {
          themeFilters = [...themeFilters, newFilter];
        }
      }
    },
  };
}
export const themeFilters = createThemeFiltersState();

function createDemoFiltersState() {
  let demoFilters: string[] = $state([]);

  return {
    get filters() {
      return demoFilters;
    },

    reset: () => {
      demoFilters = [];
    },

    applied: (): boolean => {
      return demoFilters.length > 0;
    },

    update: (newFilter: string) => {
      if (!newFilter) {
        // Clear filters if newFilter is falsy
        demoFilters = [];
        return;
      }
      if (demoFilters.includes(newFilter)) {
        demoFilters = [
          ...demoFilters.filter((filter) => filter !== newFilter),
        ];
      } else {
        demoFilters = [...demoFilters, newFilter];
      }
    },
  };
}
export const demoFilters = createDemoFiltersState();

function createMultiAnswerFiltersState() {
  let multiAnswerFilters: string[] = $state([]);

  return {
    get filters() {
      return multiAnswerFilters;
    },

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
        multiAnswerFilters = multiAnswerFilters.filter(
          (filter) => filter != newFilter,
        );
      } else {
        multiAnswerFilters = [...multiAnswerFilters, newFilter];
      }
    },
  };
}
export const multiAnswerFilters = createMultiAnswerFiltersState();
