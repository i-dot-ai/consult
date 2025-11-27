import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, cleanup, fireEvent, waitFor } from "@testing-library/svelte";

import MarkAsRead from "./MarkAsRead.svelte";

// Mock the fetch function
global.fetch = vi.fn();

// Mock the routes module
vi.mock("../../../global/routes", () => ({
  updateResponseReadStatus: vi.fn((consultationId: string, responseId: string) =>
    `/api/consultations/${consultationId}/responses/${responseId}/mark-read/`
  ),
}));

describe("MarkAsRead", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("should render children content", () => {
    const { getByText } = render(MarkAsRead, {
      consultationId: "consultation-id",
      responseId: "response-id",
    });

    // The component should render without errors
    expect(getByText).toBeDefined();
  });

  it("should call mark read API after 5 seconds on mouseenter", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValue(new Response());

    const { container } = render(MarkAsRead, {
      consultationId: "consultation-id", 
      responseId: "response-id",
    });

    const div = container.querySelector("div");
    expect(div).toBeTruthy();

    // Trigger mouseenter
    await fireEvent.mouseEnter(div!);

    // Fast-forward time by 5 seconds
    vi.advanceTimersByTime(5000);

    // Wait for async operations to complete
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/consultations/consultation-id/responses/response-id/mark-read/",
        {
          method: "POST",
        }
      );
    });
  });

  it("should not call mark read API if mouse leaves before 5 seconds", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValue(new Response());

    const { container } = render(MarkAsRead, {
      consultationId: "consultation-id",
      responseId: "response-id", 
    });

    const div = container.querySelector("div");
    expect(div).toBeTruthy();

    // Trigger mouseenter
    await fireEvent.mouseEnter(div!);

    // Fast-forward time by 3 seconds (less than 5)
    vi.advanceTimersByTime(3000);

    // Trigger mouseleave
    await fireEvent.mouseLeave(div!);

    // Fast-forward remaining time
    vi.advanceTimersByTime(3000);

    // API should not have been called
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should handle multiple mouseenter/mouseleave events correctly", async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValue(new Response());

    const { container } = render(MarkAsRead, {
      consultationId: "consultation-id",
      responseId: "response-id",
    });

    const div = container.querySelector("div");
    expect(div).toBeTruthy();

    // First mouseenter and leave
    await fireEvent.mouseEnter(div!);
    vi.advanceTimersByTime(2000);
    await fireEvent.mouseLeave(div!);

    // Second mouseenter and leave
    await fireEvent.mouseEnter(div!);
    vi.advanceTimersByTime(3000); 
    await fireEvent.mouseLeave(div!);

    // Third mouseenter, wait full 5 seconds
    await fireEvent.mouseEnter(div!);
    vi.advanceTimersByTime(5000);

    // Only one API call should be made (from the third mouseenter)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });
});