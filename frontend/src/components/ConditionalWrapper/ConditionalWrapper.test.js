import { afterEach, describe, expect, it, test } from "vitest";
import { cleanup, render } from "@testing-library/svelte";

import ConditionalWrapperTest from "./ConditionalWrapperTest.svelte";
import ConditionalWrapperStory from "./ConditionalWrapperStory.svelte";

describe("ConditionalRender", () => {
  afterEach(() => {
    cleanup();
  });

  it("should render a tag and slot if condition met", () => {
    const { container, getByText } = render(ConditionalWrapperTest, {
      element: "a",
      condition: true,
      slot: "<p>rendered</p>",
    });
    expect(container.querySelector("a")).toBeTruthy();
    expect(getByText("rendered"));
  });

  it("should not render a tag if condition not met but still render slot", () => {
    const { container, getByText } = render(ConditionalWrapperTest, {
      element: "a",
      condition: false,
      slot: "<p>rendered</p>",
    });
    expect(container.querySelector("a")).toBeFalsy();
    expect(getByText("rendered"));
  });

  it("should render story", () => {
    render(ConditionalWrapperStory);
  });
});
