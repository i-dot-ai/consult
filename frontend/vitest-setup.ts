import { vi } from "vitest";
import "@testing-library/jest-dom";

// Set required environment variables for tests
process.env.PUBLIC_ENVIRONMENT = "local";
process.env.BACKEND_URL = "http://localhost:8000";

// Mock svelte/transition to avoid Web Animations API issues in jsdom
// See: https://github.com/testing-library/svelte-testing-library/issues/416
vi.mock("svelte/transition");
