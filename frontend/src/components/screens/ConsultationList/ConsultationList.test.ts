import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationList from "./ConsultationList.svelte";
import { defaultMock, emptyMock } from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

describe("ConsultationList", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it.each(defaultMock.body.results)(
    "should render consultation",
    async (consultation) => {
      mockRoute(defaultMock);

      render(ConsultationList);

      await waitFor(() => {
        expect(screen.getByText(consultation.title)).toBeInTheDocument();
      });
    },
  );

  it("renders correct message if no consultations found", async () => {
    mockRoute(emptyMock);

    render(ConsultationList);

    await waitFor(() => {
      expect(
        screen.getByText("No consultations available"),
      ).toBeInTheDocument();
    });
  });

  it("renders error message if fetch errors", async () => {
    // retries multiple times before displaying error
    // hence the need for extended timeout
    const ERROR_MESSAGE = "Fetch Failed";
    mockRoute({ ...defaultMock, throws: new Error(ERROR_MESSAGE) });

    render(ConsultationList);

    await waitFor(
      () => {
        expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
      },
      { timeout: 20000 },
    );
  }, 20000);
});
