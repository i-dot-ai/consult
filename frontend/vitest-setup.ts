import { vi } from "vitest";
import "@testing-library/jest-dom";

// Set required environment variables for tests
process.env.PUBLIC_ENVIRONMENT = "local";
process.env.BACKEND_URL = "http://localhost:8000";

// Vitest 4.x does not include `localStorage`/`sessionStorage` in the set of
// jsdom keys copied onto `globalThis` (fixed in vitest 5). On Node 26 this
// matters because Node 26 defines a getter on `globalThis.localStorage` that
// returns `undefined` unless --localstorage-file is provided, shadowing
// jsdom's implementation. Install an in-memory shim so tests behave as they
// would in a browser. When vitest 5 is adopted this block can be removed.
function makeStorageMock() {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
}

delete (globalThis as unknown as Record<string, unknown>).localStorage;
delete (globalThis as unknown as Record<string, unknown>).sessionStorage;
Object.defineProperty(globalThis, "localStorage", {
  value: makeStorageMock(),
  configurable: true,
  writable: true,
});
Object.defineProperty(globalThis, "sessionStorage", {
  value: makeStorageMock(),
  configurable: true,
  writable: true,
});

// Mock svelte/transition to avoid Web Animations API issues in jsdom
// See: https://github.com/testing-library/svelte-testing-library/issues/416
vi.mock("svelte/transition");
