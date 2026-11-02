import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import Pagination from "./Pagination.svelte";

function renderPager(overrides: Record<string, unknown> = {}) {
  const onPageChange = vi.fn();
  const onPageSizeChange = vi.fn();
  render(Pagination, {
    id: "people",
    totalItems: 96,
    currentPage: 5,
    pageSize: 10,
    onPageChange,
    onPageSizeChange,
    ...overrides,
  });
  return { onPageChange, onPageSizeChange };
}

describe("Pagination", () => {
  it("shows the range, the first and last pages, the current page's neighbours and gaps", () => {
    renderPager();

    expect(screen.getByText("Showing 41 to 50 of 96")).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("button", { name: /^Page \d+$/ })
        .map((button) => button.textContent?.trim()),
    ).toEqual(["1", "4", "5", "6", "10"]);
    expect(screen.getAllByText("…")).toHaveLength(2);
    expect(screen.getByTestId("current-page")).toHaveTextContent("5");
    expect(screen.getByTestId("current-page")).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("moves between pages", async () => {
    const { onPageChange } = renderPager();

    await fireEvent.click(screen.getByRole("button", { name: "Page 10" }));
    await fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    await fireEvent.click(
      screen.getByRole("button", { name: "Previous page" }),
    );

    expect(onPageChange.mock.calls).toEqual([[10], [6], [4]]);
  });

  it("disables the chevrons at either end", () => {
    renderPager({ currentPage: 1, totalItems: 14 });
    expect(
      screen.getByRole("button", { name: "Previous page" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next page" })).toBeEnabled();
    expect(screen.getByText("Showing 1 to 10 of 14")).toBeInTheDocument();
  });

  it("changes the page size", async () => {
    const { onPageSizeChange } = renderPager();
    const user = userEvent.setup();

    await user.selectOptions(screen.getByLabelText("Per page"), "25");

    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });
});
