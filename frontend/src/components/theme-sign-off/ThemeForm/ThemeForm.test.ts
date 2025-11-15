import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import ThemeForm, { type Props } from "./ThemeForm.svelte";

let testData: Props;

describe("ThemeForm", () => {
  beforeEach(() => {
    testData = {
      variant: "add",
      handleConfirm: () => {},
      handleCancel: () => {},
    };
  });

  afterEach(() => cleanup());

  it("should render add variant", async () => {
    const { container, getByText } = render(ThemeForm, {
      ...testData,
    });

    expect(getByText("Add Custom Theme"));

    expect(container).toMatchSnapshot();
  });

  it("should render add variant", async () => {
    const { getByText } = render(ThemeForm, {
      ...testData,
      variant: "edit",
    });

    expect(getByText("Edit Theme"));
  });
});
