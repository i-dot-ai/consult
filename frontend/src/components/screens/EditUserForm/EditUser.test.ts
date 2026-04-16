import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import EditUserTest from "./EditUserTest.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { getMock, patchMock } from "./mocks";
import userEvent from "@testing-library/user-event";

describe("EditUser", () => {
  it("should render with userId prop", () => {
    const { container } = render(EditUserTest, { userId: "test-user-123" });
    expect(container).toBeTruthy();
  });

  it("should display error message if fetch fails", async () => {
    mockRoute(getMock);
    mockRoute({ ...patchMock, throws: new Error("Fetch failed") });

    render(EditUserTest, { userId: "test-user" });

    const user = userEvent.setup();

    await waitFor(async () => {
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("switch"));

    await waitFor(() => {
      expect(screen.getByText("failed to update user")).toBeInTheDocument();
    });

    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });
});
