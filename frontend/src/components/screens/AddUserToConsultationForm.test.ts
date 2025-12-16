import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import AddUserToConsultationForm from "./AddUserToConsultationForm.svelte";
import type { User } from "../../global/types";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("AddUserToConsultationForm", () => {
  const mockUsers: User[] = [
    {
      id: 1,
      email: "user1@example.com",
      is_staff: false,
      has_dashboard_access: false,
      created_at: "2023-01-01T00:00:00Z",
    },
    {
      id: 2,
      email: "user2@example.com",
      is_staff: true,
      has_dashboard_access: true,
      created_at: "2023-01-01T00:00:00Z",
    },
  ];

  const consultationId = "test-consultation-123";

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with users list", () => {
    render(AddUserToConsultationForm, {
      users: mockUsers,
      consultationId,
    });

    expect(screen.getByText("user1@example.com")).toBeTruthy();
    expect(screen.getByText("user2@example.com")).toBeTruthy();
    expect(screen.getByText("Add user(s)")).toBeTruthy();
  });

  it("should show error when no users selected", async () => {
    render(AddUserToConsultationForm, {
      users: mockUsers,
      consultationId,
    });

    const submitButton = screen.getByText("Add user(s)");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Please select a user to add")).toBeTruthy();
  });

  it("should submit selected users successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          message: "Successfully added 1 users to consultation",
        }),
    });

    // Mock window.location.href
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(AddUserToConsultationForm, {
      users: mockUsers,
      consultationId,
    });

    // Select first user
    const checkbox = screen.getByLabelText("user1@example.com");
    await fireEvent.click(checkbox);

    // Submit form
    const submitButton = screen.getByText("Add user(s)");
    await fireEvent.click(submitButton);

    expect(mockFetch).toHaveBeenCalledWith(
      `/api/consultations/${consultationId}/add-users/`,
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: ["1"] }),
      }),
    );
  });

  it("should handle API errors", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
    });

    render(AddUserToConsultationForm, {
      users: mockUsers,
      consultationId,
    });

    // Select first user
    const checkbox = screen.getByLabelText("user1@example.com");
    await fireEvent.click(checkbox);

    // Submit form
    const submitButton = screen.getByText("Add user(s)");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Error: 400")).toBeTruthy();
  });

  it("should handle empty users list", () => {
    render(AddUserToConsultationForm, {
      users: [],
      consultationId,
    });

    expect(screen.getByText("Add user(s)")).toBeTruthy();
    // Should not show any checkboxes
    expect(screen.queryByRole("checkbox")).toBeNull();
  });
});
