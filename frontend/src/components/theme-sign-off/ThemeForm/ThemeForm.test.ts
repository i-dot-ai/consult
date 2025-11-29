import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import ThemeForm from "./ThemeForm.svelte";

describe("ThemeForm", () => {
  const testData = {
    initialTitle: "Test Theme",
    initialDescription: "This is a test theme.",
    handleConfirm: () => {},
    handleCancel: () => {},
  };

  it("should render add variant", async () => {
    const { container, getByText } = render(ThemeForm, {
      ...testData,
      variant: "add",
    });

    expect(getByText("Add Custom Theme"));

    expect(container).toMatchSnapshot();
  });

  it("should render edit variant", async () => {
    const { getByText } = render(ThemeForm, {
      ...testData,
      variant: "edit",
    });

    expect(getByText("Edit Theme"));
  });
});
