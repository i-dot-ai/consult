import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import DeleteQuestionForm from "./DeleteQuestionForm.svelte";
import type { ConsultationResponse, Question } from "../../global/types";

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("DeleteQuestionForm", () => {
  const mockConsultation: ConsultationResponse = {
    id: "consultation-123",
    title: "Test Consultation",
    code: "test-code",
    stage: "theme_sign_off",
    users: [],
  };

  const mockQuestion: Question = {
    id: "question-456",
    number: 1,
    question_text: "What do you think about climate change?",
    has_free_text: true,
    has_multiple_choice: false,
    total_responses: 50,
    theme_status: "draft",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with consultation and question details", () => {
    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    expect(
      screen.getByText(/This question is part of the consultation with title:/),
    ).toBeTruthy();
    expect(screen.getByText("Test Consultation")).toBeTruthy();
    expect(
      screen.getByText(
        /Are you sure you want to delete the following question/,
      ),
    ).toBeTruthy();
    expect(
      screen.getByText("What do you think about climate change?"),
    ).toBeTruthy();
    expect(screen.getByText("Yes, delete it")).toBeTruthy();
    expect(screen.getByText("No, go back")).toBeTruthy();
  });

  it("should submit deletion request successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Successfully deleted question" }),
    });

    // Mock window.location.href
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    expect(mockFetch).toHaveBeenCalledWith(
      `/api/consultations/${mockConsultation.id}/questions/${mockQuestion.id}/`,
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

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const submitButton = screen.getByText("Yes, delete it");
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

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
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
      json: () => Promise.resolve({ message: "Successfully deleted question" }),
    });

    // Mock window.location.href
    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      value: mockLocation,
      writable: true,
    });

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    // Wait for the async operation to complete
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(mockLocation.href).toBe(
      `/support/consultations/${mockConsultation.id}`,
    );
  });

  it("should handle cancel button click", async () => {
    // Mock window.location.href
    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      value: mockLocation,
      writable: true,
    });

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const cancelButton = screen.getByText("No, go back");
    await fireEvent.click(cancelButton);

    expect(mockLocation.href).toBe(
      `/support/consultations/${mockConsultation.id}`,
    );
  });

  it("should handle network errors", async () => {
    const networkError = new Error("Network error");
    mockFetch.mockRejectedValueOnce(networkError);

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const submitButton = screen.getByText("Yes, delete it");
    await fireEvent.click(submitButton);

    expect(screen.getByText("Network error")).toBeTruthy();
  });

  it("should disable buttons during submission", async () => {
    // Create a promise that won't resolve immediately
    let resolvePromise: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockFetch.mockReturnValueOnce(pendingPromise);

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
    });

    const submitButton = screen.getByText("Yes, delete it");
    const cancelButton = screen.getByText("No, go back");

    await fireEvent.click(submitButton);

    // Both buttons should be disabled during submission
    expect(submitButton).toHaveProperty("disabled", true);
    expect(cancelButton).toHaveProperty("disabled", true);

    // Resolve the promise to clean up
    resolvePromise!({ ok: true });
  });

  it("should clear errors before new submission", async () => {
    // First submission with error
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: mockQuestion,
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

  it("should render with question text even when undefined", () => {
    const questionWithoutText: Question = {
      ...mockQuestion,
      question_text: undefined,
    };

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: questionWithoutText,
    });

    // Should still render the form without crashing
    expect(screen.getByText("Yes, delete it")).toBeTruthy();
    expect(screen.getByText("No, go back")).toBeTruthy();
  });

  it("should handle question with long text", () => {
    const longTextQuestion: Question = {
      ...mockQuestion,
      question_text:
        "This is a very long question that goes on and on and on and contains a lot of text to test how the component handles longer question text content that might wrap to multiple lines.",
    };

    render(DeleteQuestionForm, {
      consultation: mockConsultation,
      question: longTextQuestion,
    });

    expect(screen.getByText(/This is a very long question/)).toBeTruthy();
    expect(screen.getByText("Yes, delete it")).toBeTruthy();
  });
});
