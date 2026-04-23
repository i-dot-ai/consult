import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import DeleteUserForm from "./DeleteUserForm.svelte";
import { deleteMock, USER } from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import userEvent from "@testing-library/user-event";

describe("DeleteUserForm", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it(
    "should render delete form",
    async () => {
      mockRoute(deleteMock);

      render(DeleteUserForm, { user: USER });

      await waitFor(() => {
        expect(screen.getByText(USER.email, { exact: false })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Yes, delete user" }))
      });
    },
  );

  it(
    "should send delete request when button is clicked",
    async () => {
      const deleteBodyMock = vi.fn();
      mockRoute({...deleteMock, body: deleteBodyMock });

      render(DeleteUserForm, { user: USER });

      const user = userEvent.setup();
      await user.click(screen.getByRole("button", { name: "Yes, delete user" }));

      await waitFor(() => {
        expect(deleteBodyMock).toHaveBeenCalled();
      });
    },
  );

  it("should match snapshot initially", () => {
    mockRoute(deleteMock);

    const { container } = render(DeleteUserForm, { user: USER });
    expect(container).toMatchSnapshot();
  });
});
