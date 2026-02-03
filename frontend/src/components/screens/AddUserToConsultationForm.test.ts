import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import AddUserToConsultationForm from "./AddUserToConsultationForm.svelte";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("AddUserToConsultationForm", () => {
  const consultationId = "test-consultation-123";

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render email input form", () => {
    render(AddUserToConsultationForm, {
      consultationId,
    });

    expect(screen.getByLabelText("Email addresses")).toBeTruthy();
    expect(screen.getByText("Add users")).toBeTruthy();
  });

  it("should show error when no emails entered", async () => {
    render(AddUserToConsultationForm, {
      consultationId,
    });

    const submitButton = screen.getByText("Add users");
    await fireEvent.click(submitButton);

    expect(
      screen.getByText("Error: Please enter at least one email address."),
    ).toBeTruthy();
  });

  it("should submit emails successfully with existing users", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          message: "Added 2 users to consultation",
          added_count: 2,
          non_existent_emails: [],
          total_requested: 2,
        }),
    });

    render(AddUserToConsultationForm, {
      consultationId,
    });

    const textarea = screen.getByLabelText("Email addresses");
    await fireEvent.input(textarea, {
      target: { value: "user1@test.com, user2@test.com" },
    });

    const submitButton = screen.getByText("Add users");
    await fireEvent.click(submitButton);

    expect(mockFetch).toHaveBeenCalledWith(
      `/api/consultations/${consultationId}/add-users/`,
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emails: ["user1@test.com", "user2@test.com"] }),
      }),
    );
  });

  it("should handle non-existent users", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          message: "Added 1 users to consultation",
          added_count: 1,
          non_existent_emails: ["nonexistent@test.com"],
          total_requested: 2,
        }),
    });

    render(AddUserToConsultationForm, {
      consultationId,
    });

    const textarea = screen.getByLabelText("Email addresses");
    await fireEvent.input(textarea, {
      target: { value: "user1@test.com, nonexistent@test.com" },
    });

    const submitButton = screen.getByText("Add users");
    await fireEvent.click(submitButton);

    expect(
      screen.getByText("Successfully added 1 users to consultation."),
    ).toBeTruthy();
    expect(screen.getByText("Users not found")).toBeTruthy();
    expect(screen.getByText("nonexistent@test.com")).toBeTruthy();
    expect(screen.getByText("Copy emails")).toBeTruthy();
    expect(screen.getByText("Add these users →")).toBeTruthy();
  });

  it("should handle API errors", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: "Invalid request" }),
    });

    render(AddUserToConsultationForm, {
      consultationId,
    });

    const textarea = screen.getByLabelText("Email addresses");
    await fireEvent.input(textarea, { target: { value: "test@example.com" } });

    const submitButton = screen.getByText("Add users");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Error: Invalid request")).toBeTruthy();
  });
});
