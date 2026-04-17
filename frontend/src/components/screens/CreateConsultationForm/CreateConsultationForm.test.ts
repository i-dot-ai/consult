import { afterEach, describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";

import CreateConsultationForm from "./CreateConsultationForm.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import { defaultMock } from "./mocks";
import userEvent from "@testing-library/user-event";

describe("CreateConsultationForm", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("should render all folder options", async () => {
    const FOLDER_NAMES = ["test-folder-one", "test-folder-two"];

    mockRoute(defaultMock);

    render(CreateConsultationForm, { s3Folders: FOLDER_NAMES });

    await waitFor(() => {
      expect(screen.getByText(FOLDER_NAMES[0])).toBeInTheDocument();
      expect(screen.getByText(FOLDER_NAMES[1])).toBeInTheDocument();
    });
  });

  it("should render consultation", async () => {
    const FOLDER_NAME = "test-folder";
    const CONSULTATION_NAME = "Test Consultation";

    mockRoute(defaultMock);

    render(CreateConsultationForm, { s3Folders: [FOLDER_NAME] });

    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText("Consultation name"),
      CONSULTATION_NAME,
    );

    const select = screen.getByLabelText("S3 folder (consultation code)");

    await fireEvent.change(select, { target: { value: FOLDER_NAME } });

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(
        screen.getByText(`${CONSULTATION_NAME} is being set up`, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });
  });

  it("should render error text if fetch fails", async () => {
    const ERROR_MESSAGE = "Fetch Failed";
    const FOLDER_NAME = "test-folder";
    const CONSULTATION_NAME = "Test Consultation";

    mockRoute({ ...defaultMock, throws: new Error(ERROR_MESSAGE) });

    render(CreateConsultationForm, { s3Folders: [FOLDER_NAME] });

    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText("Consultation name"),
      CONSULTATION_NAME,
    );

    const select = screen.getByLabelText("S3 folder (consultation code)");

    await fireEvent.change(select, { target: { value: FOLDER_NAME } });

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });
  });

  it("should render status error text if fetch fails", async () => {
    const ERROR_MESSAGE = "Server Error";
    const FOLDER_NAME = "test-folder";
    const CONSULTATION_NAME = "Test Consultation";

    mockRoute({
      ...defaultMock,
      status: 500,
      body: { message: ERROR_MESSAGE },
    });

    render(CreateConsultationForm, { s3Folders: [FOLDER_NAME] });

    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText("Consultation name"),
      CONSULTATION_NAME,
    );

    const select = screen.getByLabelText("S3 folder (consultation code)");

    await fireEvent.change(select, { target: { value: FOLDER_NAME } });

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText(ERROR_MESSAGE)).toBeInTheDocument();
    });
  });
});
