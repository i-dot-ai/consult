import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ThemeForm from "./ThemeForm.svelte";
import ThemeFormStory from "./ThemeFormStory.svelte";

describe("ThemeForm", () => {
  const baseProps = {
    handleConfirm: () => {},
    handleCancel: () => {},
  };

  const mockTheme = {
    id: "test-id",
    name: "Test Theme",
    description: "This is a test theme.",
    version: 1,
    last_modified_by: "test@example.com",
    modified_at: new Date().toISOString(),
  };

  it("should render add variant", async () => {
    const { container } = render(ThemeForm, {
      ...baseProps,
      variant: "add",
    });

    expect(screen.getByText("Add Custom Theme")).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });

  it("should render edit variant", async () => {
    render(ThemeForm, {
      ...baseProps,
      variant: "edit",
      theme: mockTheme,
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
      "theme",
      "handleConfirm",
      "handleCancel",
    ]);
  });
});
