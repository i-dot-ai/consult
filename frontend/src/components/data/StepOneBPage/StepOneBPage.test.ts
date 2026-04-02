import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import StepOneBPage from "./StepOneBPage.svelte";

describe("StepOneBPage", () => {
  const CONTINUE_BUTTON_TEXT = "My data is ready to upload";
  const PREV_LEARNING_BUTTON_TEXT = "Previous Learning";
  const getLearningButtonText = (learningNumber: number) =>
    `Learning ${learningNumber}`;
  const LEARNING_TITLES = [
    "Senior Policy Analyst",
    "Consultation Lead",
    "Data Manager",
  ];

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

    expect(screen.getByText(LEARNING_TITLES[0])).toBeInTheDocument();

    expect(screen.queryByText(LEARNING_TITLES[1])).not.toBeInTheDocument();

    expect(screen.queryByText(LEARNING_TITLES[2])).not.toBeInTheDocument();
  });

  it("should render next learning when next button is clicked", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", { name: "Next Learning" });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(LEARNING_TITLES[1])).toBeInTheDocument();
    });
  });

  it("should render last learning when prev button is clicked on first item", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", {
      name: PREV_LEARNING_BUTTON_TEXT,
    });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(LEARNING_TITLES[2])).toBeInTheDocument();
    });
  });

  it("should render respective learning if its learning button is clicked", async () => {
    render(StepOneBPage);

    const nextButton = screen.getByRole("button", {
      name: getLearningButtonText(3),
    });
    const user = userEvent.setup();
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(LEARNING_TITLES[2])).toBeInTheDocument();
    });
  });

  it("should disable continue button initially", () => {
    render(StepOneBPage);

    const continueButton = screen.getByRole("button", {
      name: CONTINUE_BUTTON_TEXT,
    });
    expect(continueButton).toBeDisabled();
  });

  it("should enable continue button if all checkboxes are checked", async () => {
    render(StepOneBPage);

    const checkboxes = screen.getAllByRole("checkbox");
    const user = userEvent.setup();

    for (const checkbox of checkboxes) {
      await user.click(checkbox);
    }

    const continueButtons = screen.getAllByRole("button", {
      name: CONTINUE_BUTTON_TEXT,
    });

    await waitFor(() => {
      continueButtons.forEach(continueButton => {
        expect(continueButton).toBeInTheDocument();
        expect(continueButton).not.toBeDisabled();
      })
    });
  });

  it("should keep continue button disabled if only some checkboxes are checked", async () => {
    render(StepOneBPage);

    const checkboxes = screen.getAllByRole("checkbox");
    const user = userEvent.setup();

    for (const checkbox of checkboxes.slice(0, checkboxes.length / 2)) {
      await user.click(checkbox);
    }

    const continueButton = screen.getByRole("button", {
      name: CONTINUE_BUTTON_TEXT,
    });

    await waitFor(() => {
      expect(continueButton).toBeDisabled();
    });
  });

  it("should match snapshot", () => {
    const { container } = render(StepOneBPage);
    expect(container).toMatchSnapshot();
  });
});
