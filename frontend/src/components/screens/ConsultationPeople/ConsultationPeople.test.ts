import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import ConsultationPeople from "./ConsultationPeople.svelte";
import {
  COLLEAGUE,
  CONSULTATION_ID,
  CREATOR,
  YOU,
  userAssignmentMock,
  consultationErrorMock,
  invitedConsultationMock,
  manyPeopleConsultationMock,
  ownedConsultationMock,
  userRemovalErrorMock,
  userRemovalMock,
  staffUserMock,
  userMock,
} from "./mocks";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

const TEST_DATA = {
  consultationId: CONSULTATION_ID,
  backHref: `/consultations/${CONSULTATION_ID}`,
  backText: "Back to the consultation",
};
const defaultQueryOptions = queryClient.getDefaultOptions();

async function renderLoaded(props: typeof TEST_DATA) {
  const view = render(ConsultationPeople, props);
  await waitFor(() => {
    expect(screen.getByText(/Future homes standard · /)).toBeInTheDocument();
  });
  return view;
}

function getRowTexts() {
  return screen
    .getAllByRole("row")
    .slice(1)
    .map((row) => row.textContent?.replace(/\s+/g, " ").trim());
}

function getRequests(method: string) {
  return fetchMock.callHistory
    .calls()
    .filter((call) => (call.options.method ?? "GET").toUpperCase() === method)
    .map((call) => ({
      url: call.url,
      body: call.options.body ? JSON.parse(call.options.body as string) : null,
    }));
}

async function openAddPeople() {
  await fireEvent.click(screen.getByRole("button", { name: "Add people" }));
  return screen.getByRole("dialog");
}

async function typeEmails(dialog: HTMLElement, text: string) {
  await fireEvent.input(within(dialog).getByLabelText("Email addresses"), {
    target: { value: text },
  });
}

async function confirmAdd(dialog: HTMLElement) {
  await fireEvent.click(
    within(dialog).getByRole("button", { name: "Add people" }),
  );
}

describe("ConsultationPeople", () => {
  beforeEach(() => {
    // A failed fetch would otherwise retry for seconds before the page shows it.
    queryClient.setDefaultOptions({
      queries: { ...defaultQueryOptions.queries, retry: false },
    });
  });

  afterEach(() => {
    queryClient.setDefaultOptions(defaultQueryOptions);
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    fetchMock.clearHistory();
    queryClient.resetQueries();
  });

  it("lists the creator first, tags them, and marks the current user", async () => {
    mockRoute(invitedConsultationMock);
    mockRoute(userMock);
    await renderLoaded(TEST_DATA);

    expect(screen.getByText("People on this consultation")).toBeInTheDocument();
    expect(
      screen.getByText("Future homes standard · 3 people"),
    ).toBeInTheDocument();
    expect(getRowTexts()).toEqual([
      `${CREATOR.email} Creator`,
      COLLEAGUE.email,
      `${YOU.email} (you)`,
    ]);
  });

  it("lets the owner add and remove people, but never the creator", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    await renderLoaded(TEST_DATA);

    expect(
      screen.getByRole("button", { name: "Add people" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: `Remove ${COLLEAGUE.email}` }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: `Remove ${CREATOR.email}` }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: `Remove ${YOU.email}` }),
    ).not.toBeInTheDocument();
    expect(getRowTexts()[0]).toBe(`${YOU.email} (you) Creator`);
  });

  it("shows an invited user the list only", async () => {
    mockRoute(invitedConsultationMock);
    mockRoute(userMock);
    await renderLoaded(TEST_DATA);

    expect(
      screen.getByText(
        "The person who created this consultation adds and removes people.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Add people" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^Remove / }),
    ).not.toBeInTheDocument();
  });

  it("lets staff manage a consultation they did not create", async () => {
    mockRoute(invitedConsultationMock);
    mockRoute(staffUserMock);
    await renderLoaded(TEST_DATA);

    expect(
      screen.getByRole("button", { name: "Add people" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: `Remove ${COLLEAGUE.email}` }),
    ).toBeInTheDocument();
  });

  it("links back to wherever the page says it came from", async () => {
    mockRoute(invitedConsultationMock);
    mockRoute(userMock);
    const { unmount } = await renderLoaded(TEST_DATA);
    expect(screen.getByLabelText("Back to the consultation")).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}`,
    );
    unmount();

    await renderLoaded({
      ...TEST_DATA,
      backHref: `/consultations/${CONSULTATION_ID}/data-upload`,
      backText: "Back to data set-up",
    });
    expect(screen.getByLabelText("Back to data set-up")).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}/data-upload`,
    );
  });

  it("refuses an empty or malformed list of email addresses", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    mockRoute(userAssignmentMock);
    await renderLoaded(TEST_DATA);
    const dialog = await openAddPeople();

    expect(
      within(dialog).getByText(
        "They can see Future homes standard and work on it.",
      ),
    ).toBeInTheDocument();
    await confirmAdd(dialog);
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "Enter at least one email address",
    );

    await typeEmails(dialog, "not-an-email, sam.kaur@example.gov.uk");
    await confirmAdd(dialog);
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "Enter email addresses in the right format, like name@example.gov.uk. Check not-an-email",
    );
    expect(within(dialog).getByLabelText("Email addresses")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(getRequests("POST")).toEqual([]);
  });

  it("adds the people and names the ones already on the consultation", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    mockRoute(userAssignmentMock);
    await renderLoaded(TEST_DATA);
    const dialog = await openAddPeople();

    await typeEmails(
      dialog,
      `Jo.Patel@example.gov.uk ${COLLEAGUE.email}\nlee.okafor@example.gov.uk, jo.patel@example.gov.uk`,
    );
    await confirmAdd(dialog);

    await waitFor(() => {
      expect(getRequests("POST")).toEqual([
        {
          url: expect.stringContaining(
            `/consultations/${CONSULTATION_ID}/assign-users/`,
          ),
          body: {
            emails: ["jo.patel@example.gov.uk", "lee.okafor@example.gov.uk"],
          },
        },
      ]);
    });
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        `2 people added. ${COLLEAGUE.email} is already on this consultation.`,
      );
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      getRequests("GET").filter((request) =>
        request.url.endsWith(`/consultations/${CONSULTATION_ID}/`),
      ),
    ).toHaveLength(2);
  });

  it("still reports the people added when the list cannot be refreshed", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    await renderLoaded(TEST_DATA);
    fetchMock.removeRoutes();
    mockRoute(consultationErrorMock);
    mockRoute(userMock);
    mockRoute(userAssignmentMock);
    const dialog = await openAddPeople();

    await typeEmails(
      dialog,
      "jo.patel@example.gov.uk lee.okafor@example.gov.uk",
    );
    await confirmAdd(dialog);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("2 people added.");
    });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The people on this consultation could not be loaded.",
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("adds nobody when every address is already on the consultation", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    mockRoute(userAssignmentMock);
    await renderLoaded(TEST_DATA);
    const dialog = await openAddPeople();

    await typeEmails(dialog, `${COLLEAGUE.email}; ${CREATOR.email}`);
    await confirmAdd(dialog);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        `Nobody added. ${COLLEAGUE.email}, ${CREATOR.email} are already on this consultation.`,
      );
    });
    expect(getRequests("POST")).toEqual([]);
  });

  it("removes a person after confirming", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    mockRoute(userRemovalMock(COLLEAGUE.id));
    await renderLoaded(TEST_DATA);

    await fireEvent.click(
      screen.getByRole("button", { name: `Remove ${COLLEAGUE.email}` }),
    );
    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).getByText(
        `${COLLEAGUE.email} can no longer see Future homes standard. They can be added again.`,
      ),
    ).toBeInTheDocument();

    await fireEvent.click(
      within(dialog).getByRole("button", { name: "Remove" }),
    );

    await waitFor(() => {
      expect(getRequests("DELETE")).toEqual([
        {
          url: expect.stringContaining(
            `/consultations/${CONSULTATION_ID}/users/?user_id=${COLLEAGUE.id}`,
          ),
          body: null,
        },
      ]);
    });
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        `${COLLEAGUE.email} removed.`,
      );
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows an error when removing fails", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    mockRoute(userRemovalErrorMock(COLLEAGUE.id));
    await renderLoaded(TEST_DATA);

    const removeButton = screen.getByRole("button", {
      name: `Remove ${COLLEAGUE.email}`,
    });
    removeButton.focus();
    await fireEvent.click(removeButton);
    await fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: "Remove",
      }),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        `${COLLEAGUE.email} was not removed. Try again.`,
      );
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(removeButton).toHaveFocus();
  });

  it("pages the list only when there are more than ten people", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    const { unmount } = await renderLoaded(TEST_DATA);
    expect(
      screen.queryByRole("navigation", { name: "Pagination" }),
    ).not.toBeInTheDocument();
    unmount();
    fetchMock.removeRoutes();
    queryClient.resetQueries();

    mockRoute(manyPeopleConsultationMock);
    mockRoute(userMock);
    await renderLoaded(TEST_DATA);
    expect(
      screen.getByText("Future homes standard · 12 people"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Pagination" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("current-page")).toHaveTextContent("1");
    expect(screen.getByRole("button", { name: "Page 2" })).toBeInTheDocument();
    expect(screen.getByText("Showing 1 to 10 of 12")).toBeInTheDocument();
    expect(getRowTexts()).toHaveLength(10);
  });

  it("shows an error when the consultation cannot be loaded", async () => {
    mockRoute(consultationErrorMock);
    mockRoute(userMock);
    render(ConsultationPeople, TEST_DATA);

    await waitFor(() => {
      expect(
        screen.getByText(
          "The people on this consultation could not be loaded.",
        ),
      ).toBeInTheDocument();
    });
  });

  it("matches snapshot", async () => {
    mockRoute(ownedConsultationMock);
    mockRoute(userMock);
    const { container } = await renderLoaded(TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
