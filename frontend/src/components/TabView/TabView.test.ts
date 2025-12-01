import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import TabView from "./TabView.svelte";
import Star from "../svg/material/Star.svelte";
import Finance from "../svg/material/Finance.svelte";

describe("TabView", () => {
  it("should call handleClick func", async () => {
    const user = userEvent.setup();
    const handleChangeMock = vi.fn();

    render(TabView, {
      value: "star-tab",
      tabs: [
        { id: "star-tab", title: "Star Tab", icon: Star },
        { id: "finance-tab", title: "Finance Tab", icon: Finance },
      ],
      handleChange: handleChangeMock,
    });

    expect(screen.getByText("Star Tab")).toBeInTheDocument();
    expect(screen.getByText("Finance Tab")).toBeInTheDocument();
    expect(screen.getAllByRole("img").length).toBe(2);

    const tabButtons = await screen.findAllByRole("tab");
    const starTab = tabButtons.at(0);
    const financeTab = tabButtons.at(1);
    await user.click(financeTab);

    expect(handleChangeMock).toHaveBeenCalledTimes(2);
    expect(handleChangeMock).toHaveBeenCalledWith("finance-tab");

    await user.click(starTab);
    expect(handleChangeMock).toHaveBeenCalledTimes(4);
    expect(handleChangeMock).toHaveBeenCalledWith("star-tab");
  });

  it("should not render icons if no icon is passed", async () => {
    render(TabView, {
      value: "star-tab",
      tabs: [
        { id: "star-tab", title: "Star Tab" },
        { id: "finance-tab", title: "Finance Tab" },
      ],
    });

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
