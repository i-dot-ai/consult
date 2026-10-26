import type { Consultation, User } from "./types";

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
        demoFilters = [...demoFilters.filter((filter) => filter !== newFilter)];
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

export function createUserState(
  userData: User | undefined,
  consultationData: Consultation | undefined,
) {
  if (!userData || !consultationData) {
    return;
  }

  const createdBy = consultationData?.created_by;
  const createdByEmail =
    typeof createdBy === "string" ? createdBy : createdBy?.email;

  const userIsOwner = userData?.email === createdByEmail;
  const userIsAdmin = userData?.is_staff;

  // eslint-disable-next-line svelte/prefer-svelte-reactivity
  const createdAtText = new Date(
    consultationData?.created_at,
  ).toLocaleDateString("en-GB");

  let createdByText = createdByEmail;
  if (!createdByEmail) {
    createdByText = "an unknown user";
  }
  if (userIsOwner) {
    createdByText = "you";
  }

  return {
    get createdByEmail() {
      return createdByEmail;
    },
    get isOwner() {
      return userIsOwner;
    },
    get isAdmin() {
      return userIsAdmin;
    },
    get createdAtText() {
      return createdAtText;
    },
    get createdByText() {
      return createdByText;
    },
  };
}
