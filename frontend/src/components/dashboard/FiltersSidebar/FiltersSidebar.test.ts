import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import FiltersSidebar from "./FiltersSidebar.svelte";

describe("FiltersSidebar", () => {
  const testData = {
    showEvidenceRich: true,
    demoOptions: { country: ["england", "scotland"] },
    demoData: { country: { england: 10, scotland: 20 } },
    evidenceRich: false,
    unseenResponsesOnly: false,
    loading: false,
  };

  it("should render data", () => {
    render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      unseenResponsesOnly: testData.unseenResponsesOnly,
      loading: testData.loading,
    });
    Object.keys(testData.demoData).forEach((category) => {
      expect(screen.getByText(category)).toBeInTheDocument();
      Object.keys(testData.demoData[category]).forEach((rowKey) => {
        expect(screen.getByText(rowKey)).toBeInTheDocument();
        expect(
          screen.getByText(testData.demoData[category][rowKey]),
        ).toBeInTheDocument();
      });
    });
    expect(screen.getByText("Show evidence rich")).toBeInTheDocument();
  });

  it("should not render data if loading", () => {
    render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      unseenResponsesOnly: testData.unseenResponsesOnly,
      loading: true,
    });
    Object.keys(testData.demoData).forEach((category) => {
      expect(screen.queryByText(category)).toBeNull();
      Object.keys(testData.demoData[category]).forEach((rowKey) => {
        expect(screen.queryByText(rowKey)).toBeNull();
        expect(
          screen.queryByText(testData.demoData[category][rowKey]),
        ).toBeNull();
      });
    });
    expect(screen.getByText("Show evidence rich")).toBeInTheDocument();
  });

  it("should not render evidence rich switch if not show evidence rich", () => {
    render(FiltersSidebar, {
      showEvidenceRich: false,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
    });

    expect(screen.queryByText("Show evidence rich")).not.toBeInTheDocument();
  });

  it("should call set evidence rich func", async () => {
    const user = userEvent.setup();
    const setEvidenceRichMock = vi.fn();
    const setUnseenResponsesMock = vi.fn();

    render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      unseenResponsesOnly: testData.unseenResponsesOnly,
      setEvidenceRich: setEvidenceRichMock,
      setUnseenResponses: setUnseenResponsesMock,
    });
    expect(setEvidenceRichMock).toHaveBeenCalledTimes(1);
    expect(setEvidenceRichMock).toHaveBeenCalledWith(false);

    const evidenceRichButton = screen.getByRole("switch", {
      name: /evidence rich/i,
    });
    await user.click(evidenceRichButton);

    expect(setEvidenceRichMock).toHaveBeenCalledTimes(2);
    expect(setEvidenceRichMock).toHaveBeenCalledWith(true);
  });

  it("should call set unseen responses func", async () => {
    const user = userEvent.setup();
    const setEvidenceRichMock = vi.fn();
    const setUnseenResponsesMock = vi.fn();

    render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      showUnseenResponse: true,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      unseenResponsesOnly: testData.unseenResponsesOnly,
      setEvidenceRich: setEvidenceRichMock,
      setUnseenResponses: setUnseenResponsesMock,
    });
    expect(setUnseenResponsesMock).toHaveBeenCalledTimes(1);
    expect(setUnseenResponsesMock).toHaveBeenCalledWith(false);

    const unseenResponsesButton = screen.getByRole("switch", {
      name: /show unseen responses/i,
    });
    await user.click(unseenResponsesButton);

    expect(setUnseenResponsesMock).toHaveBeenCalledTimes(2);
    expect(setUnseenResponsesMock).toHaveBeenCalledWith(true);
  });

  it("should not render unseen responses switch if not show unseen response", () => {
    render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      showUnseenResponse: false,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      unseenResponsesOnly: testData.unseenResponsesOnly,
    });

    expect(screen.queryByText("Show unseen responses")).not.toBeInTheDocument();
  });
});
