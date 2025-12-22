import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import DeleteConsultationForm from "./DeleteConsultationForm.svelte";
import type { ConsultationResponse } from "../../global/types";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("DeleteConsultationForm", () => {
  const mockConsultation: ConsultationResponse = {
    id: "consultation-123",
    title: "Test Consultation",
    code: "test-code",
    stage: "theme_sign_off",
    users: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with consultation details", () => {
    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    expect(
      screen.getByText(/Are you sure you want to delete this consultation:/),
    ).toBeTruthy();
    expect(screen.getByText("Test Consultation")).toBeTruthy();
    expect(screen.getByText("Yes, delete it")).toBeTruthy();
  });

  it("should submit deletion request successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ message: "Successfully deleted consultation" }),
    });

    // Mock window.location.href
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    expect(mockFetch).toHaveBeenCalledWith(
      `/api/consultations/${mockConsultation.id}/`,
      expect.objectContaining({
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("should handle API errors", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Error: 500")).toBeTruthy();
  });

  it("should show loading state during submission", async () => {
    // Create a promise that won't resolve immediately
    let resolvePromise: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockFetch.mockReturnValueOnce(pendingPromise);

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText("Deleting...")).toBeTruthy();

    // Resolve the promise to clean up
    resolvePromise!({ ok: true });
  });

  it("should redirect after successful deletion", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ message: "Successfully deleted consultation" }),
    });

    // Mock window.location.href
    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      value: mockLocation,
      writable: true,
    });

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    // Wait for the async operation to complete
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(mockLocation.href).toBe("/support/consultations");
  });

  it("should handle network errors", async () => {
    const networkError = new Error("Network error");
    mockFetch.mockRejectedValueOnce(networkError);

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Network error")).toBeTruthy();
  });

  it("should disable button during submission", async () => {
    // Create a promise that won't resolve immediately
    let resolvePromise: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockFetch.mockReturnValueOnce(pendingPromise);

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    // Button should be disabled during submission
    expect(submitButton).toHaveProperty("disabled", true);

    // Resolve the promise to clean up
    resolvePromise!({ ok: true });
  });

  it("should clear errors before new submission", async () => {
    // First submission with error
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(DeleteConsultationForm, {
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    // Error should be visible
    expect(screen.getByText("Error: 500")).toBeTruthy();

    // Second submission (successful)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Success" }),
    });

    // Mock window.location.href
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    await fireEvent.click(submitButton);

    // Error should be cleared (will throw if still present)
    expect(() => screen.getByText("Error: 500")).toThrow();
  });
});
