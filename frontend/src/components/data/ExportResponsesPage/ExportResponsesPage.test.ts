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

const originalV2Flag = process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "true";

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

  it("renders step 1 with Qualtrics selected when nothing is saved", () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    expect(
      screen.getByRole("heading", {
        name: /Step 1 of 5: Export the responses/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Happens outside Consult")).toBeInTheDocument();
    expect(screen.getByLabelText(/Qualtrics/)).toBeChecked();
    expect(
      screen.getByRole("heading", { name: "Exporting from Qualtrics" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Exporting from Citizen Space" }),
    ).not.toBeInTheDocument();
  });

  it("preselects the saved provider", () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: "citizen-space",
    });

    expect(screen.getByLabelText(/Citizen Space/)).toBeChecked();
    expect(
      screen.getByRole("heading", { name: "Exporting from Citizen Space" }),
    ).toBeInTheDocument();
  });

  it("swaps the instructions when another provider is picked", async () => {
    render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    await fireEvent.click(screen.getByLabelText(/Citizen Space/));

    expect(
      screen.getByRole("heading", { name: "Exporting from Citizen Space" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Exporting from Qualtrics" }),
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

    await fireEvent.click(screen.getByLabelText(/Citizen Space/));
    await fireEvent.click(
      screen.getByRole("button", { name: "Continue to preparing your data" }),
    );

    await waitFor(() => {
      expect(window.location.href).toBe(
        `/consultations/${CONSULTATION_ID}/data-upload`,
      );
    });
    const [call] = fetchMock.callHistory.calls();
    expect(call.url).toContain(`/api/v2/consultations/${CONSULTATION_ID}/`);
    expect(call.options.method).toMatch(/^patch$/i);
    expect(JSON.parse(call.options.body as string)).toEqual({
      data_source: "citizen-space",
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
      expect(screen.getByText("There is a problem")).toBeInTheDocument();
    });
    expect(window.location.href).toBe("");
    expect(
      screen.getByRole("button", { name: "Continue to preparing your data" }),
    ).not.toBeDisabled();
  });

  it("matches snapshot", () => {
    const { container } = render(ExportResponsesPage, {
      consultationId: CONSULTATION_ID,
      dataSource: null,
    });

    expect(container).toMatchSnapshot();
  });
});
