import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup } from "@testing-library/svelte";

import RespondentSidebar, { type Props } from "./RespondentSidebar.svelte";
import RespondentSidebarStory from "./RespondentSidebarStory.svelte";
import { getPercentage } from "../../../global/utils";

let testData: Props;

describe("RespondentSidebar", () => {
  beforeEach(() => {
    testData = {
      demoData: [
        { name: "country", value: "england" },
        { name: "age", value: "25-35" },
      ],
      stakeholderName: "Test stakeholder",
      questionsAnswered: 10,
      totalQuestions: 20,
    };
  });

  afterEach(() => cleanup());

  it("should render data", () => {
    const { getByText } = render(RespondentSidebar, {
      ...testData,
    });

    testData.demoData.forEach((dataItem) => {
      expect(getByText(dataItem.name));
      expect(getByText(dataItem.value));
    });
    expect(getByText(testData.stakeholderName));

    const partialNum = testData.questionsAnswered;
    const totalNum = testData.totalQuestions;
    const percentage = getPercentage(partialNum, totalNum);
    const countsText = `${percentage}% (${partialNum}/${totalNum})`;
    expect(getByText(countsText));
  });

  it("should render editable mode and call update callback", async () => {
    vi.mock("svelte/transition");
    const user = userEvent.setup();
    const updateMock = vi.fn();

    const { getByTestId, getByLabelText } = render(RespondentSidebar, {
      ...testData,
      updateStakeholderName: updateMock,
    });

    // click to reveal buttons and text input
    const editButton = getByTestId("edit-button");
    await user.click(editButton);

    // clear existing subtitle and type new one
    const subtitleInput = getByLabelText("Edit Subtitle");
    await user.clear(subtitleInput);
    await user.type(subtitleInput, "New Stakeholder");

    // click to save subtitle
    const saveButton = getByTestId("save-button");
    await user.click(saveButton);

    // check if subtitle is updated correctly
    expect(updateMock).toHaveBeenCalledWith("New Stakeholder");
  });

  it("should render story", () => {
    render(RespondentSidebarStory);
  });
});
