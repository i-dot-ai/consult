import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import EditUserTest from "./EditUserTest.svelte";

describe("EditUser", () => {
  it("should render with userId prop", () => {
    const { container } = render(EditUserTest, { userId: "test-user-123" });
    expect(container).toBeTruthy();
  });
});
