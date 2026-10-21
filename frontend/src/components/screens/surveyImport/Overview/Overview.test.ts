import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import Overview from "./Overview.svelte";
import { CONSULTATION_ID, consultationMock, userMock } from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../../global/utils";
import { queryClient } from "../../../../global/queryClient";

describe("Overview", () => {
  const TEST_DATA = {
    consultationId: CONSULTATION_ID,
  };

  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("should render consultation title", async () => {
    mockRoute(consultationMock);
    mockRoute(userMock);

    render(Overview, TEST_DATA);

    await waitFor(() => {
      expect(
        screen.getByText(consultationMock.body.title, { exact: false }),
      ).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    mockRoute(consultationMock);
    mockRoute(userMock);

    const { container } = render(Overview, TEST_DATA);
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    mockRoute(consultationMock);
    mockRoute(userMock);

    const { container } = render(Overview, TEST_DATA);

    await waitFor(() => {
      expect(
        screen.getByText(consultationMock.body.title, { exact: false }),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
