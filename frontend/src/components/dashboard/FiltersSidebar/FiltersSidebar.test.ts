import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import FiltersSidebar from "./FiltersSidebar.svelte";

describe("FiltersSidebar", () => {
  const demographics = [
    { id: "1", name: "country", value: "england", count: 10 },
    { id: "2", name: "country", value: "scotland", count: 20 },
  ];

  it("should render demographic data", () => {
    render(FiltersSidebar, {
      demographics,
      loading: false,
    });

    expect(screen.getByText("country")).toBeInTheDocument();
    expect(screen.getByText("england")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("scotland")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("should show full skeleton when loading with no data", () => {
    render(FiltersSidebar, {
      demographics: [],
      loading: true,
    });

    expect(screen.queryByText("country")).not.toBeInTheDocument();
  });

  it("should show counts loading when loading with existing data", () => {
    render(FiltersSidebar, {
      demographics,
      loading: true,
    });

    expect(screen.getByText("country")).toBeInTheDocument();
    expect(screen.getByText("england")).toBeInTheDocument();
    expect(screen.getByText("scotland")).toBeInTheDocument();
    expect(screen.queryByText("10")).not.toBeInTheDocument();
    expect(screen.queryByText("20")).not.toBeInTheDocument();
  });
});
