import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import AssignThemesForm from "./AssignThemesForm.svelte";
import { CONSULTATION_ID, assignMock } from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import userEvent from "@testing-library/user-event";

const CONSULTATIONS = [{
  id: CONSULTATION_ID,
  title: "Folder One",
  code: "folder-one",
}]

describe("AssignThemesForm", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("should render assign themes form", async () => {
    mockRoute(assignMock);

    render(AssignThemesForm, { consultations: CONSULTATIONS });

    await waitFor(() => {
      expect(
        screen.getByText(CONSULTATIONS[0].title, { exact: false }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Assign Themes" }),
      ).toBeInTheDocument();
    });
  });

  it("should send post request when button is clicked", async () => {
    const findBodyMock = vi.fn();
    mockRoute({ ...assignMock, body: findBodyMock });

    render(AssignThemesForm, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.selectOptions(screen.getByRole('combobox'), [CONSULTATIONS[0].id])
    await user.click(screen.getByRole("button", { name: "Assign Themes" }));

    await waitFor(() => {
      expect(findBodyMock).toHaveBeenCalled();
    });
  });

  it("should display error msg if error", async () => {
    mockRoute({ ...assignMock, throws: new Error("Error") });

    render(AssignThemesForm, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.selectOptions(screen.getByRole('combobox'), [CONSULTATIONS[0].id])
    await user.click(screen.getByRole("button", { name: "Assign Themes" }));

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    mockRoute(assignMock);

    const { container } = render(AssignThemesForm, { consultations: CONSULTATIONS });
    expect(container).toMatchSnapshot();
  });
});
