import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import FindThemesForm from "./FindThemesForm.svelte";
import { CONSULTATION_ID, findMock } from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import userEvent from "@testing-library/user-event";

const CONSULTATIONS = [{
  id: CONSULTATION_ID,
  title: "Folder One",
  code: "folder-one",
}]

describe("FindThemesForm", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("should render find themes form", async () => {
    mockRoute(findMock);

    render(FindThemesForm, { consultations: CONSULTATIONS });

    await waitFor(() => {
      expect(
        screen.getByText(CONSULTATIONS[0].title, { exact: false }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Find Themes" }),
      ).toBeInTheDocument();
    });
  });

  it("should send post request when button is clicked", async () => {
    const findBodyMock = vi.fn();
    mockRoute({ ...findMock, body: findBodyMock });

    render(FindThemesForm, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.selectOptions(screen.getByRole('combobox'), [CONSULTATIONS[0].id])
    await user.click(screen.getByRole("button", { name: "Find Themes" }));

    await waitFor(() => {
      expect(findBodyMock).toHaveBeenCalled();
    });
  });

  it("should display error msg if error", async () => {
    mockRoute({ ...findMock, throws: new Error("Error") });

    render(FindThemesForm, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.selectOptions(screen.getByRole('combobox'), [CONSULTATIONS[0].id])
    await user.click(screen.getByRole("button", { name: "Find Themes" }));

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    mockRoute(findMock);

    const { container } = render(FindThemesForm, { consultations: CONSULTATIONS });
    expect(container).toMatchSnapshot();
  });
});
