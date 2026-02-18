import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import Learnings from "./Learnings.svelte";

describe("Learnings", () => {
  const testData = {
    items: [
      {
        text: "Taking time to prepare our data correctly at the start saved us hours during the analysis phase. We were able to jump straight into insights rather than troubleshooting data issues.",
        author: "Senior Policy Analyst",
        organisation: "Department for Education",
      },
      {
        text: "Having consistent question formatting across all responses made the AI theme detection incredibly accurate. It's worth the extra 20 minutes to get this right.",
        author: "Consultation Lead",
        organisation: "Department for Transport",
      },
      {
        text: "We collated responses from three different survey platforms into one file. The standardised structure meant the tool handled everything seamlessly.",
        author: "Data Manager",
        organisation: "Ministry of Justice",
      }
    ],
  };

  it("should render learning text", () => {
    render(Learnings, testData);

    expect(screen.getByText(`"${testData.items.at(0)!.text}"`)).toBeInTheDocument();
  });

  it("should render learning author", () => {
    render(Learnings, testData);

    expect(screen.getByText(testData.items.at(0)!.author)).toBeInTheDocument();
  });

  it("should render learning organisation", () => {
    render(Learnings, testData);

    expect(screen.getByText(testData.items.at(0)!.organisation)).toBeInTheDocument();
  });

  it("should render first learning only", () => {
    render(Learnings, testData);

    expect(screen.getByText(`"${testData.items.at(0)!.text}"`)).toBeInTheDocument();

    testData.items.slice(1).forEach(item => {
      expect(screen.queryByText(`"${item.text}"`)).not.toBeInTheDocument();
    })
  });

  it("should render same number of buttons as items", () => {
    render(Learnings, testData);

    expect(screen.getAllByTestId("Learnings Button")).toHaveLength(testData.items.length);
  });

  it.each(["Previous Learning", "Next Learning"])("should render button", (label) => {
    render(Learnings, testData);

    expect(screen.getByLabelText(label)).toBeInTheDocument();
  });

  it("should show next step if next button is clicked", async () => {
    const user = userEvent.setup();
    render(Learnings, testData);
    
    const nextButton = screen.getByLabelText("Next Learning");
    await user.click(nextButton);

    waitFor(() => {
      expect(screen.getByText(testData.items.at(1)!.text)).toBeInTheDocument();
      expect(screen.getByText(testData.items.at(0)!.text)).not.toBeInTheDocument();
    })
  });

  it("should show previous step if previous button is clicked", async () => {
    const user = userEvent.setup();
    render(Learnings, testData);
    
    const nextButton = screen.getByLabelText("Previous Learning");
    await user.click(nextButton);

    waitFor(() => {
      expect(screen.getByText(testData.items.at(-1)!.text)).toBeInTheDocument();
      expect(screen.getByText(testData.items.at(0)!.text)).not.toBeInTheDocument();
    })
  });

  it("should show respective step if a step button is clicked", async () => {
    const user = userEvent.setup();
    render(Learnings, testData);
    
    const nextButton = screen.getByLabelText("Learning 2");
    await user.click(nextButton);

    waitFor(() => {
      expect(screen.getByText(testData.items.at(1)!.text)).toBeInTheDocument();
      expect(screen.getByText(testData.items.at(0)!.text)).not.toBeInTheDocument();
    })
  });
});
