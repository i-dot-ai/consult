import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ThemeForm from "./ThemeForm.svelte";

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
});
