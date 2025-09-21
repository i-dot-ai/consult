import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen } from "@testing-library/svelte";

import FiltersSidebar from "./FiltersSidebar.svelte";

let testData;

describe("FiltersSidebar", () => {
  beforeEach(() => {
    testData = {
      showEvidenceRich: true,
      demoOptions: { country: ["england", "scotland"] },
      demoData: { country: { england: 10, scotland: 20 } },
      evidenceRich: false,
      loading: false,
    };
  });

  afterEach(() => cleanup());

  it("should render data", () => {
    const { getByText } = render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      loading: testData.loading,
    });
    Object.keys(testData.demoData).forEach((category) => {
      expect(getByText(category));
      Object.keys(testData.demoData[category]).forEach((rowKey) => {
        expect(getByText(rowKey));
        expect(getByText(testData.demoData[category][rowKey]));
      });
    });
    expect(getByText("Show evidence rich"));
  });

  it("should not render data if loading", () => {
    const { getByText, queryByText } = render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      loading: true,
    });
    Object.keys(testData.demoData).forEach((category) => {
      expect(queryByText(category)).toBeNull();
      Object.keys(testData.demoData[category]).forEach((rowKey) => {
        expect(queryByText(rowKey)).toBeNull();
        expect(queryByText(testData.demoData[category][rowKey])).toBeNull();
      });
    });
    expect(getByText("Show evidence rich"));
  });

  it("should not render evidence rich switch if not show evidence rich", () => {
    const { queryByText } = render(FiltersSidebar, {
      showEvidenceRich: false,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
    });

    expect(queryByText("Show evidence rich"));
  });

  it("should call set evidence rich func", async () => {
    const user = userEvent.setup();
    const setEvidenceRichMock = vi.fn();

    const { getByText, queryByText } = render(FiltersSidebar, {
      showEvidenceRich: testData.showEvidenceRich,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      evidenceRich: testData.evidenceRich,
      setEvidenceRich: setEvidenceRichMock,
    });
    expect(setEvidenceRichMock).toHaveBeenCalledTimes(1);
    expect(setEvidenceRichMock).toHaveBeenCalledWith(false);

    const evidenceRichButton = screen.getByRole("switch");
    await user.click(evidenceRichButton);

    expect(setEvidenceRichMock).toHaveBeenCalledTimes(2);
    expect(setEvidenceRichMock).toHaveBeenCalledWith(true);
  });
});
