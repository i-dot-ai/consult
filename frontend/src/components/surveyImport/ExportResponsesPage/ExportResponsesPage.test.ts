import {
  afterAll,
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import ExportResponsesPage from "./ExportResponsesPage.svelte";
import { CONSULTATION_ID, updateErrorMock, updateMock } from "./mocks";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

// Hoisted so the mocks module resolves the v2 URL when it is imported.
const originalV2Flag = vi.hoisted(() => {
  const original = process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
  process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "true";
  return original;
});

describe("ExportResponsesPage", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { href: "", origin: window.location.origin });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  afterAll(() => {
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = originalV2Flag;
  });

  it("renders step 1 with Citizen Space selected when nothing is saved", () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    expect(screen.getByText("Step 1 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Export the responses" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Happens outside Consult")).toBeInTheDocument();
    expect(screen.getByLabelText(/Citizen Space/)).toBeChecked();
    expect(
      screen.getByRole("heading", { name: "Exporting from Citizen Space" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Exporting from Qualtrics" }),
    ).not.toBeInTheDocument();
  });

  it("preselects the saved provider", () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: "qualtrics",
    });

    expect(screen.getByLabelText(/Qualtrics/)).toBeChecked();
    expect(
      screen.getByRole("heading", { name: "Exporting from Qualtrics" }),
    ).toBeInTheDocument();
  });

  it("swaps the instructions when another provider is picked", async () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    await fireEvent.click(screen.getByLabelText(/Qualtrics/));

    expect(
      screen.getByRole("heading", { name: "Exporting from Qualtrics" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Exporting from Citizen Space" }),
    ).not.toBeInTheDocument();
  });

  it("links back to the data upload overview", () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    expect(
      screen.getByRole("link", { name: "Back to overview" }),
    ).toHaveAttribute("href", `/consultations/${CONSULTATION_ID}/data-upload`);
  });

  it("saves the chosen provider and returns to the overview", async () => {
    mockRoute(updateMock);
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    await fireEvent.click(screen.getByLabelText(/Qualtrics/));
    await fireEvent.click(
      screen.getByRole("button", { name: "Continue to preparing your data" }),
    );

    await waitFor(() => {
      expect(window.location.href).toBe(
        `/consultations/${CONSULTATION_ID}/data-upload/checks`,
      );
    });
    const [call] = fetchMock.callHistory.calls();
    expect(call.url).toContain(`/api/v2/consultations/${CONSULTATION_ID}/`);
    expect(call.options.method).toMatch(/^patch$/i);
    expect(JSON.parse(call.options.body as string)).toEqual({
      data_source: "qualtrics",
    });
  });

  it("shows an error and stays on the page when saving fails", async () => {
    mockRoute(updateErrorMock);
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    await fireEvent.click(
      screen.getByRole("button", { name: "Continue to preparing your data" }),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Your choice was not saved",
      );
    });
    expect(window.location.href).toBe("");
    expect(screen.getByLabelText(/Citizen Space/)).toBeChecked();
    expect(
      screen.getByRole("link", { name: "contact support" }),
    ).toHaveAttribute("href", "mailto:consult@cabinetoffice.gov.uk");
    expect(
      screen.getByRole("button", { name: "Continue to preparing your data" }),
    ).not.toBeDisabled();
  });

  it("re-enables Continue when the page is restored from the back-forward cache", async () => {
    mockRoute(updateMock);
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });
    const continueButton = screen.getByRole("button", {
      name: "Continue to preparing your data",
    });

    await fireEvent.click(continueButton);
    await waitFor(() => {
      expect(window.location.href).toBe(
        `/consultations/${CONSULTATION_ID}/data-upload/checks`,
      );
    });
    expect(continueButton).toBeDisabled();

    window.dispatchEvent(
      Object.assign(new Event("pageshow"), { persisted: true }),
    );

    await waitFor(() => {
      expect(continueButton).not.toBeDisabled();
    });
  });

  it("matches snapshot", () => {
    const { container } = render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    expect(container).toMatchSnapshot();
  });
});
