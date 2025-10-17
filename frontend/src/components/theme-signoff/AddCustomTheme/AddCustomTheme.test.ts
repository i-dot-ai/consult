import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import AddCustomTheme, { type Props } from "./AddCustomTheme.svelte";

let testData: Props;

describe("AddCustomTheme", () => {
  beforeEach(() => {
    testData = {
      variant: "add",
      handleConfirm: () => {},
      handleCancel: () => {},
    };
  });

  afterEach(() => cleanup());

  it("should render add variant", async () => {
    const { container, getByText } = render(AddCustomTheme, {
      ...testData,
    });

    expect(getByText("Add Custom Theme"));

    expect(container).toMatchSnapshot();
  });

  it("should render add variant", async () => {
    const { container, getByText } = render(AddCustomTheme, {
      ...testData,
      variant: "edit",
    });

    expect(getByText("Edit Theme"));
  });
});
