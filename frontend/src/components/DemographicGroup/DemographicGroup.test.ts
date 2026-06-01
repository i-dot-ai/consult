import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import DemographicGroup from "./DemographicGroup.svelte";

describe("DemographicGroup", () => {
  const items = [
    { id: "1", name: "Region", value: "North", count: 100 },
    { id: "2", name: "Region", value: "South", count: 200 },
    { id: "3", name: "Region", value: "East", count: 50 },
  ];

  it("should render category and option labels with counts", () => {
    render(DemographicGroup, {
      category: "Region",
      items,
    });

    expect(screen.getByText("Region")).toBeInTheDocument();
    expect(screen.getByText("North")).toBeInTheDocument();
    expect(screen.getByText("South")).toBeInTheDocument();
    expect(screen.getByText("East")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("50")).toBeInTheDocument();
  });

  it("should show labels but hide counts when countsLoading is true", () => {
    render(DemographicGroup, {
      category: "Region",
      items,
      countsLoading: true,
    });

    expect(screen.getByText("Region")).toBeInTheDocument();
    expect(screen.getByText("North")).toBeInTheDocument();
    expect(screen.getByText("South")).toBeInTheDocument();
    expect(screen.getByText("East")).toBeInTheDocument();
    expect(screen.queryByText("100")).not.toBeInTheDocument();
    expect(screen.queryByText("200")).not.toBeInTheDocument();
    expect(screen.queryByText("50")).not.toBeInTheDocument();
  });
});
