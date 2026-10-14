import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import OutsideConsultTag from "./OutsideConsultTag.svelte";

describe("OutsideConsultTag", () => {
  it("renders the label", () => {
    render(OutsideConsultTag);

    expect(screen.getByText("Happens outside Consult")).toBeInTheDocument();
  });

  it("matches snapshot", () => {
    const { container } = render(OutsideConsultTag);

    expect(container).toMatchSnapshot();
  });
});
