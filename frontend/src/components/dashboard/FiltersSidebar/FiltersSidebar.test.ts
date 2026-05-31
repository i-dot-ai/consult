import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import FiltersSidebar from "./FiltersSidebar.svelte";

describe("FiltersSidebar", () => {
  const demographics = [
    { id: "1", name: "country", value: "england", count: 10 },
    { id: "2", name: "country", value: "scotland", count: 20 },
  ];

  it("should render data", () => {
    render(FiltersSidebar, {
      showEvidenceRich: true,
      demographics,
      evidenceRich: false,
      unseenResponses: false,
      loading: false,
    });

    expect(screen.getByText("country")).toBeInTheDocument();
    expect(screen.getByText("england")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("scotland")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("Show evidence rich")).toBeInTheDocument();
  });

  it("should show full skeleton when loading with no data", () => {
    render(FiltersSidebar, {
      showEvidenceRich: true,
      demographics: [],
      evidenceRich: false,
      unseenResponses: false,
      loading: true,
    });

    expect(screen.queryByText("country")).not.toBeInTheDocument();
    expect(screen.getByText("Show evidence rich")).toBeInTheDocument();
  });

  it("should show counts loading when loading with existing data", () => {
    render(FiltersSidebar, {
      showEvidenceRich: true,
      demographics,
      evidenceRich: false,
      unseenResponses: false,
      loading: true,
    });

    expect(screen.getByText("country")).toBeInTheDocument();
    expect(screen.getByText("england")).toBeInTheDocument();
    expect(screen.getByText("scotland")).toBeInTheDocument();
    expect(screen.queryByText("10")).not.toBeInTheDocument();
    expect(screen.queryByText("20")).not.toBeInTheDocument();
  });

  it("should not render evidence rich switch if not show evidence rich", () => {
    render(FiltersSidebar, {
      showEvidenceRich: false,
      demographics,
      evidenceRich: false,
      loading: false,
    });

    expect(screen.queryByText("Show evidence rich")).not.toBeInTheDocument();
  });

  it("should call set evidence rich func", async () => {
    const user = userEvent.setup();
    const setEvidenceRichMock = vi.fn();
    const setUnseenResponsesMock = vi.fn();

    render(FiltersSidebar, {
      showEvidenceRich: true,
      demographics,
      evidenceRich: false,
      unseenResponses: false,
      setEvidenceRich: setEvidenceRichMock,
      setUnseenResponses: setUnseenResponsesMock,
      loading: false,
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
      showEvidenceRich: true,
      showUnseenResponse: true,
      demographics,
      evidenceRich: false,
      unseenResponses: false,
      setEvidenceRich: setEvidenceRichMock,
      setUnseenResponses: setUnseenResponsesMock,
      loading: false,
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
      showEvidenceRich: true,
      showUnseenResponse: false,
      demographics,
      evidenceRich: false,
      unseenResponses: false,
      loading: false,
    });

    expect(screen.queryByText("Show unseen responses")).not.toBeInTheDocument();
  });
});
