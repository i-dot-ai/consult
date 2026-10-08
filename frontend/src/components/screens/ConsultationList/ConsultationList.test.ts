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
        screen.getByText("You have no consultations yet"),
      ).toBeInTheDocument();
    });

    const addConsultationLinks = screen.getAllByRole("link", {
      name: "Add consultation",
    });
    expect(addConsultationLinks).toHaveLength(2);
    addConsultationLinks.forEach((link) =>
      expect(link).toHaveAttribute("href", "/consultations/new"),
    );
  });

  it("shows one add consultation button when consultations exist", async () => {
    mockRoute(defaultMock);

    render(ConsultationList);

    await waitFor(() => {
      expect(
        screen.getByText(defaultMock.body.results[0].title, { exact: false }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByRole("link", { name: "Add consultation" }),
    ).toHaveAttribute("href", "/consultations/new");
  });

  it("hides the add consultation button(s) when enableV2 is false", async () => {
    mockRoute(emptyMock);

    render(ConsultationList, { enableV2: false });

    await waitFor(() => {
      expect(
        screen.getByText("You have no consultations yet"),
      ).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("link", { name: "Add consultation" }),
    ).not.toBeInTheDocument();
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

  it("should match snapshot initially", () => {
    mockRoute(defaultMock);

    const { container } = render(ConsultationList);
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    mockRoute(defaultMock);

    const { container } = render(ConsultationList);

    await waitFor(() => {
      expect(
        screen.getAllByText(defaultMock.body.results[0].title, { exact: false })
          .length,
      ).toBeGreaterThan(0);
    });
    expect(container).toMatchSnapshot();
  });
});
