import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import AddConsultationForm from "./AddConsultationForm.svelte";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import { consultationsV2QueryParts } from "../../../global/queries/consultations/parts";

const URL = consultationsV2QueryParts.url();

const EXISTING = {
  id: "4d1414d5-9300-447b-b788-50d0bef7e807",
  title: "Future homes standard",
  created_at: "2026-08-18T10:00:00Z",
  created_by: { id: 1, email: "admin@example.com", is_staff: true },
  is_owner: true,
};

const DUPLICATE_NAME = "future homes STANDARD";
const DUPLICATE_URL = `${URL}?${new URLSearchParams({ title__iexact: DUPLICATE_NAME })}`;

const duplicateMock = {
  url: DUPLICATE_URL,
  body: { count: 1, next: null, previous: null, results: [EXISTING] },
};

describe("AddConsultationForm", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: { href: "", origin: originalLocation.origin },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("renders the name field and actions", () => {
    render(AddConsultationForm);

    expect(
      screen.getByRole("heading", { name: "Add a consultation" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Consultation name")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save and continue" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Cancel" })).toBeInTheDocument();
  });

  it("disables save until the name has non-whitespace content", async () => {
    render(AddConsultationForm);

    const saveButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    expect(saveButton).toBeDisabled();

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: "   " },
    });
    expect(saveButton).toBeDisabled();

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: "Brand new" },
    });
    expect(saveButton).toBeEnabled();
  });

  it("warns when the name matches an existing consultation", async () => {
    mockRoute(duplicateMock);
    render(AddConsultationForm);

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: DUPLICATE_NAME },
    });

    await waitFor(() => {
      expect(
        screen.getByText("Future homes standard already exists."),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: "Save anyway" }),
    ).toBeInTheDocument();
  });

  it("notes when several consultations share the name", async () => {
    mockRoute({
      url: DUPLICATE_URL,
      body: {
        count: 3,
        next: null,
        previous: null,
        results: [EXISTING],
      },
    });
    render(AddConsultationForm);

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: DUPLICATE_NAME },
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Showing the most recent of 3 with this name/),
      ).toBeInTheDocument();
    });
  });

  it("creates the consultation and redirects to its detail page", async () => {
    mockRoute({
      url: URL,
      method: "POST",
      body: { id: "new-id", title: "Brand new" },
      status: 201,
    });
    render(AddConsultationForm);

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: "  Brand new  " },
    });
    await fireEvent.click(
      screen.getByRole("button", { name: "Save and continue" }),
    );

    await waitFor(() => {
      expect(window.location.href).toBe("/consultations/new-id");
    });

    const postCall = fetchMock.callHistory.lastCall(URL, { method: "POST" });
    expect(JSON.parse(postCall?.options.body as string)).toEqual({
      title: "Brand new",
    });
  });

  it("shows an error if creation fails", async () => {
    mockRoute({ url: URL, method: "POST", body: {}, status: 500 });
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    render(AddConsultationForm);

    await fireEvent.input(screen.getByLabelText("Consultation name"), {
      target: { value: "Brand new" },
    });
    await fireEvent.click(
      screen.getByRole("button", { name: "Save and continue" }),
    );

    await waitFor(() => {
      expect(
        screen.getByText("Failed to create consultation"),
      ).toBeInTheDocument();
    });
    consoleError.mockRestore();
  });
});
