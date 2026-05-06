import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import RemoveUserFromConsultationForm from "./RemoveUserFromConsultationForm.svelte";
import type { User, ConsultationResponse } from "../../global/types";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("RemoveUserFromConsultationForm", () => {
  const mockUser: User = {
    id: 1,
    email: "user@example.com",
    is_staff: false,
    created_at: "2023-01-01T00:00:00Z",
  };

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

  it("should render with user and consultation details", () => {
    render(RemoveUserFromConsultationForm, {
      user: mockUser,
      consultation: mockConsultation,
    });

    expect(screen.getByText(/Are you sure you want to remove/)).toBeTruthy();
    expect(screen.getByText("user@example.com")).toBeTruthy();
    expect(screen.getByText("Test Consultation")).toBeTruthy();
    expect(screen.getByText("Yes, remove them")).toBeTruthy();
  });

  it("should submit removal request successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Successfully removed user" }),
    });

    // Mock window.location.href
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(RemoveUserFromConsultationForm, {
      user: mockUser,
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, remove them");
    await fireEvent.click(submitButton);

    expect(mockFetch).toHaveBeenCalledWith(
      `/api/consultations/${mockConsultation.id}/users/${mockUser.id}/`,
      expect.objectContaining({
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("should handle API errors", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    render(RemoveUserFromConsultationForm, {
      user: mockUser,
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, remove them");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Error: 404")).toBeTruthy();
  });

  it("should show loading state during submission", async () => {
    // Create a promise that won't resolve immediately
    let resolvePromise: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockFetch.mockReturnValueOnce(pendingPromise);

    render(RemoveUserFromConsultationForm, {
      user: mockUser,
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, remove them");
    await fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText("Removing...")).toBeTruthy();

    // Resolve the promise to clean up
    resolvePromise!({ ok: true });
  });

  it("should redirect after successful removal", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Successfully removed user" }),
    });

    // Mock window.location.href
    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      value: mockLocation,
      writable: true,
    });

    render(RemoveUserFromConsultationForm, {
      user: mockUser,
      consultation: mockConsultation,
    });

    const submitButton = screen.getByText("Yes, remove them");
    await fireEvent.click(submitButton);

    // Wait for the async operation to complete
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(mockLocation.href).toBe(
      `/support/consultations/${mockConsultation.id}`,
    );
  });
});
