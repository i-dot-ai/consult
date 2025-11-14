import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/svelte";

import ConditionalWrapperTestHelper from "./ConditionalWrapperTestHelper.svelte";
import ConditionalWrapperStory from "./ConditionalWrapperStory.svelte";

describe("ConditionalRender", () => {
  afterEach(() => {
    cleanup();
  });

  it("should render a tag and slot if condition met", () => {
    const { container, getByText } = render(ConditionalWrapperTestHelper, {
      element: "a",
      condition: true,
      content: "rendered",
    });

    expect(container.querySelector("a")).toBeTruthy();
    expect(getByText("rendered")).toBeTruthy();
  });

  it("should not render a tag if condition not met but still render slot", () => {
    const { container, getByText } = render(ConditionalWrapperTestHelper, {
      element: "a",
      condition: false,
      content: "rendered",
    });

    expect(container.querySelector("a")).toBeFalsy();
    expect(getByText("rendered")).toBeTruthy();
  });

  it("should render story", () => {
    render(ConditionalWrapperStory);
  });
});
