import { vi } from "vitest";

// Mock svelte/transition to avoid Web Animations API issues in jsdom
// See: https://github.com/testing-library/svelte-testing-library/issues/416
vi.mock("svelte/transition");
