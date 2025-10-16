import { afterEach, describe, expect, it } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import EditUserTest from "./EditUserTest.svelte";

describe("EditUser", () => {
  afterEach(() => cleanup());

  it("should render with userId prop", () => {
    const { container } = render(EditUserTest, { userId: "test-user-123" });
    expect(container).toBeTruthy();
  });
});
