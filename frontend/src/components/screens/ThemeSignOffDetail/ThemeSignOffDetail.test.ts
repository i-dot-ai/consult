import { beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ThemeSignOffDetail from "./ThemeSignOffDetail.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { candidateThemesGetMock, questionMock, candidateThemeSelectMock, selectedThemesGetMock, CONSULTATION_ID, QUESTION_ID, selectedThemesCreateMock, selectedThemesEditMock, selectedThemesDeleteMock, flatten } from "./mocks";
import userEvent from "@testing-library/user-event";

function setupMocks() {
  [candidateThemesGetMock, questionMock, candidateThemeSelectMock, selectedThemesGetMock, selectedThemesCreateMock, selectedThemesEditMock, selectedThemesDeleteMock].forEach(mock => mockRoute(mock));
}
function clearMocks() {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("EditUser", () => {

  beforeEach(() => {
    clearMocks();
  })

  it.each(selectedThemesGetMock.body().results)("should render selected themes", async (selectedTheme) => {
    setupMocks();

    render(ThemeSignOffDetail, { consultationId: CONSULTATION_ID, questionId: QUESTION_ID });

    await waitFor(() => {
      expect(screen.getByText(selectedTheme.name)).toBeInTheDocument();
    })
  });

  it.each(flatten(candidateThemesGetMock.body().results))("should render candidate themes", async (candidateTheme) => {
    setupMocks();

    render(ThemeSignOffDetail, { consultationId: CONSULTATION_ID, questionId: QUESTION_ID });

    await waitFor(() => {
      expect(screen.getByText(candidateTheme.name)).toBeInTheDocument();
    })
  });

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    expect(container).toMatchSnapshot();
  })

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(ThemeSignOffDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(screen.getByText(
        selectedThemesGetMock.body().results[0].name
      )).toBeInTheDocument();
    })
    expect(container).toMatchSnapshot();
  })
});
