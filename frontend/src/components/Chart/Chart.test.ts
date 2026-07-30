import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import { setupVitestCanvasMock } from "vitest-canvas-mock";
import { DATA, LABELS, LEGEND_ID, INTERACTIVE } from "./testData";
import userEvent from "@testing-library/user-event";
import Chart from "./ChartTest.svelte";

// Mock the ResizeObserver
const ResizeObserverMock = class ResizeObserver {
  observe = vi.fn();
};

// Stub the global ResizeObserver
vi.stubGlobal("ResizeObserver", ResizeObserverMock);

describe("Chart", () => {
  const testData = {
    data: DATA,
    labels: LABELS,
    legendId: LEGEND_ID,
    interactive: INTERACTIVE,
  };

  beforeEach(() => {
    vi.resetAllMocks();
    setupVitestCanvasMock();
  });

  it.each(LABELS)("should render label text", async (label) => {
    render(Chart, testData);

    await waitFor(() => {
      expect(screen.getByText(label.text)).toBeInTheDocument();
    });
  });

  it("should disable item on click if interactive", async () => {
    render(Chart, {
      data: DATA,
      labels: LABELS,
      legendId: LEGEND_ID,
      interactive: true,
    });

    expect(screen.getByText("first item")).not.toHaveClass("line-through");

    const legendItemButton = screen.getByTestId(
      "chart-legend-item-clickable-first item",
    );
    const user = userEvent.setup();
    await user.click(legendItemButton);

    await waitFor(() => {
      expect(screen.getByText("first item")).toHaveClass("line-through");
    });
  });

  it("should not disable item on click if not interactive", async () => {
    render(Chart, {
      data: DATA,
      labels: LABELS,
      legendId: LEGEND_ID,
      interactive: false,
    });

    expect(screen.getByText("first item")).not.toHaveClass("line-through");

    const legendItemButton = screen.getByTestId(
      "chart-legend-item-static-first item",
    );
    const user = userEvent.setup();
    await user.click(legendItemButton);

    await waitFor(() => {
      expect(screen.getByText("first item")).not.toHaveClass("line-through");
    });
  });

  it("should match snapshot initially", () => {
    const { container } = render(Chart, {
      data: DATA,
      labels: LABELS,
      legendId: LEGEND_ID,
      interactive: INTERACTIVE,
    });
    expect(container).toMatchSnapshot();

    // Canvas snapshots
    const canvasEl = screen.getByTestId("chart-canvas") as HTMLCanvasElement;
    const context = canvasEl!.getContext("2d");

    const canvasEvents = context!.__getEvents();
    expect(canvasEvents).toMatchSnapshot();

    const canvasCalls = context!.__getDrawCalls();
    expect(canvasCalls).toMatchSnapshot();
  });
});
