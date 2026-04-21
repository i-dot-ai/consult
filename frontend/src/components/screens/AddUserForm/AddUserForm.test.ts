import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import AddUserForm from "./AddUserForm.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import { defaultMock } from "./mocks";
import userEvent from "@testing-library/user-event";

describe("AddUserForm", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("should send user email as request body", async () => {
    const USER_EMAIL = "user@test.com";

    const submitMock = vi.fn();
    mockRoute({
      ...defaultMock,
      callback: submitMock,
    }),

    render(AddUserForm);

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Email addresses"), USER_EMAIL);

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(submitMock).toHaveBeenCalledWith(
        expect.objectContaining({
          "body": `{\"email\":\"${USER_EMAIL}\",\"is_staff\":false}`,
        })
      )
    });
  });

  it("should display error text", async () => {
    const USER_EMAIL = "user@test.com";
    const FETCH_ERROR = "Fetch Failed";

    mockRoute({
      ...defaultMock,
      throws: new Error(FETCH_ERROR),
    }),

    render(AddUserForm);

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Email addresses"), USER_EMAIL);

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText(`Error: ${FETCH_ERROR}`)).toBeInTheDocument();
    });
  });
});
