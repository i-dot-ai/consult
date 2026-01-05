import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ThemeForm from "./ThemeForm.svelte";
import ThemeFormStory from "./ThemeFormStory.svelte";

describe("ThemeForm", () => {
  const testData = {
    initialTitle: "Test Theme",
    initialDescription: "This is a test theme.",
    handleConfirm: () => {},
    handleCancel: () => {},
  };

  it("should render add variant", async () => {
    const { container } = render(ThemeForm, {
      ...testData,
      variant: "add",
    });

    expect(screen.getByText("Add Custom Theme")).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });

  it("should render edit variant", async () => {
    render(ThemeForm, {
      ...testData,
      variant: "edit",
    });

    expect(screen.getByText("Edit Theme")).toBeInTheDocument();
  });

  it("should have a story configured correctly", () => {
    expect(ThemeFormStory).toHaveProperty("name", "ThemeForm");
    expect(ThemeFormStory).toHaveProperty("component", ThemeForm);
    expect(ThemeFormStory).toHaveProperty("props");

    const propsDefined = ThemeFormStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "variant",
      "initialTitle",
      "initialDescription",
      "handleConfirm",
      "handleCancel",
    ]);
  });
});
