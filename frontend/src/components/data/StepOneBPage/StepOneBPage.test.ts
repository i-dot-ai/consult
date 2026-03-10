import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import StepOneBPage from "./StepOneBPage.svelte";

describe("StepOneBPage", () => {
  it("should render order number text", () => {
    render(StepOneBPage);

    expect(
      screen.getByText("Step 1b: Prepare and get to know your data"),
    ).toBeInTheDocument();
  });

  it("should render learnings title", () => {
    render(StepOneBPage);

    expect(
      screen.getByText("What other departments have found:"),
    ).toBeInTheDocument();
  });

  it("should initially render first learning only", () => {
    render(StepOneBPage);

    expect(screen.getByText("Senior Policy Analyst")).toBeInTheDocument();

    expect(screen.queryByText("Consultation Lead")).not.toBeInTheDocument();

    expect(screen.queryByText("Data Manager")).not.toBeInTheDocument();
  });

  it("should render next learning when next button is clicked", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", { name: "Next Learning" });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText("Consultation Lead")).toBeInTheDocument();
    });
  });

  it("should render last learning when prev button is clicked on first item", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", {
      name: "Previous Learning",
    });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText("Data Manager")).toBeInTheDocument();
    });
  });

  it("should render respective learning if its learning button is clicked", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", { name: "Learning 3" });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText("Data Manager")).toBeInTheDocument();
    });
  });

  it("should match snapshot", () => {
    const { container } = render(StepOneBPage);
    expect(container).toMatchSnapshot();
  });
});
