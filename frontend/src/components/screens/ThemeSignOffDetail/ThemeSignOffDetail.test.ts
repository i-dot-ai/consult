import { beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ThemeSignOffDetail from "./ThemeSignOffDetail.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import {
  candidateThemesGetMock,
  questionMock,
  candidateThemeSelectMock,
  selectedThemesGetMock,
  CONSULTATION_ID,
  QUESTION_ID,
  selectedThemesCreateMock,
  selectedThemesEditMock,
  selectedThemesDeleteMock,
  flatten,
  answersGetMock,
} from "./mocks";
import userEvent from "@testing-library/user-event";

const mocks = {
  candidateThemesGetMock,
  questionMock,
  candidateThemeSelectMock,
  selectedThemesGetMock,
  selectedThemesCreateMock,
  selectedThemesEditMock,
  selectedThemesDeleteMock,
  answersGetMock,
};

function setupMocks() {
  Object.values(mocks).forEach((mock) => mockRoute(mock));
}
function clearMocks() {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("EditUser", () => {
  beforeEach(() => {
    clearMocks();
  });

  it.each(selectedThemesGetMock.body().results)(
    "should render selected themes",
    async (selectedTheme) => {
      setupMocks();

      render(ThemeSignOffDetail, {
        consultationId: CONSULTATION_ID,
        questionId: QUESTION_ID,
      });

      await waitFor(() => {
        expect(screen.getByText(selectedTheme.name)).toBeInTheDocument();
      });
    },
  );

  it.each(flatten(candidateThemesGetMock.body().results))(
    "should render candidate themes",
    async (candidateTheme) => {
      setupMocks();

      render(ThemeSignOffDetail, {
        consultationId: CONSULTATION_ID,
        questionId: QUESTION_ID,
      });

      await waitFor(() => {
        expect(screen.getByText(candidateTheme.name)).toBeInTheDocument();
      });
    },
  );

  it("should render conflict error", async () => {
    Object.values({
      ...mocks,
      selectedThemesEditMock: {
        ...selectedThemesEditMock,
        status: 412,
        body: {
          last_modified_by: {
            email: "someotheruser@test.com",
          },
          latest_version: 5,
        },
      },
    }).forEach((mock) => mockRoute(mock));

    render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    const user = userEvent.setup();

    let selectedThemeEditButton;
    await waitFor(() => {
      selectedThemeEditButton = screen
        .getAllByTestId("selected-theme-edit-button")
        .at(0);
    });

    await user.click(selectedThemeEditButton!);

    await waitFor(() => {
      expect(screen.getAllByRole("textbox").length).toBeGreaterThan(0);
    });

    for (const textbox of screen.getAllByRole("textbox")) {
      await user.type(textbox, "test");
    }

    const saveButton = screen.getByRole("button", { name: "Save Changes" });
    await user.click(saveButton);

    // TODO: Investigate double modal
    await waitFor(() => {
      expect(
        screen.getAllByText("Theme Conflict Detected").length,
      ).toBeGreaterThan(0);
    });
  });

  it("should render 404 error", async () => {
    Object.values({
      ...mocks,
      selectedThemesEditMock: {
        ...selectedThemesEditMock,
        status: 404,
        body: undefined,
      },
    }).forEach((mock) => mockRoute(mock));

    render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    const user = userEvent.setup();

    let selectedThemeEditButton;
    await waitFor(() => {
      selectedThemeEditButton = screen
        .getAllByTestId("selected-theme-edit-button")
        .at(0);
    });

    await user.click(selectedThemeEditButton!);

    await waitFor(() => {
      expect(screen.getAllByRole("textbox").length).toBeGreaterThan(0);
    });

    for (const textbox of screen.getAllByRole("textbox")) {
      await user.type(textbox, "test");
    }

    const saveButton = screen.getByRole("button", { name: "Save Changes" });
    await user.click(saveButton);

    // TODO: Investigate double modal
    await waitFor(() => {
      expect(screen.getAllByText("Theme Deselected").length).toBeGreaterThan(0);
    });
  });

  it("should update selected theme details", async () => {
    setupMocks();

    render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    const user = userEvent.setup();

    let selectedThemeEditButton;
    await waitFor(() => {
      selectedThemeEditButton = screen
        .getAllByTestId("selected-theme-edit-button")
        .at(0);
    });

    await user.click(selectedThemeEditButton!);

    await waitFor(() => {
      expect(screen.getAllByRole("textbox").length).toBeGreaterThan(0);
    });

    const textboxes = screen.getAllByRole("textbox");
    await user.type(textboxes[0], "test title");
    await user.type(textboxes[1], "test description");

    const saveButton = screen.getByRole("button", { name: "Save Changes" });
    await user.click(saveButton);

    await waitFor(() => {
      expect(
        screen.getByText("test title", { exact: false }),
      ).toBeInTheDocument();
      expect(
        screen.getByText("test description", { exact: false }),
      ).toBeInTheDocument();
      expect(screen.getByText("Edited")).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(selectedThemesGetMock.body().results[0].name),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
