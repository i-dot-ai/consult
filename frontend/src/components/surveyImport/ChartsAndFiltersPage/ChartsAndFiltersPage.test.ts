import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import ChartsAndFiltersPage from "./ChartsAndFiltersPage.svelte";
import {
  AGREEMENT_ANSWERS,
  CONSULTATION_ID,
  MERGED_RESPONDENT_ANSWERS,
  PENALTY_ANSWERS,
  QUESTIONS,
  REGION_ANSWERS,
  RESPONDENT_ANSWERS,
  SCALE_ANSWERS,
  answersErrorMock,
  answersMock,
  mergeErrorMock,
  mergeMock,
  questionsErrorMock,
  questionsMock,
  updateErrorMock,
  updateMock,
} from "./mocks";
import type { QuestionV2 } from "../../../global/queries/questions/types";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

const TEST_DATA = { consultationId: CONSULTATION_ID };

function mockAnswers(regionAnswers = REGION_ANSWERS) {
  mockRoute(answersMock("q1-uuid", AGREEMENT_ANSWERS));
  mockRoute(answersMock("q2-uuid", regionAnswers));
  mockRoute(answersMock("q3-uuid", RESPONDENT_ANSWERS));
  mockRoute(answersMock("q7-uuid", PENALTY_ANSWERS));
}

async function renderLoaded(questions: QuestionV2[] = QUESTIONS) {
  mockRoute({ ...questionsMock, body: questions });
  const view = render(ChartsAndFiltersPage, TEST_DATA);
  await waitFor(() => {
    expect(
      screen.getByRole("button", { name: /^Question 2\b/ }),
    ).toBeInTheDocument();
  });
  return view;
}

async function waitForAnswers() {
  await waitFor(() => {
    expect(screen.getAllByText("3 answers")).toHaveLength(2);
  });
}

function questionButton(number: number) {
  return screen.getByRole("button", {
    name: new RegExp(`^Question ${number}\\b`),
  });
}

async function expandQuestion(number: number) {
  await fireEvent.click(questionButton(number));
}

function cellTexts(row: HTMLElement) {
  return within(row)
    .getAllByRole("cell")
    .map((cell) => cell.textContent?.replace(/\s+/g, " ").trim() ?? "");
}

function answerRows() {
  return screen.getAllByRole("row").map((row) =>
    cellTexts(row)
      .filter((text) => text !== "")
      .join(" "),
  );
}

function answerNames() {
  return screen.getAllByRole("row").map((row) => cellTexts(row)[1]);
}

function requests(method: string) {
  return fetchMock.callHistory
    .calls()
    .filter((call) => (call.options.method ?? "").toUpperCase() === method)
    .map((call) => ({
      url: call.url,
      body: JSON.parse(call.options.body as string),
    }));
}

function withShortName(questionId: string, shortName: string) {
  return QUESTIONS.map((question) =>
    question.id === questionId
      ? { ...question, short_name: shortName }
      : question,
  );
}

const defaultQueryOptions = queryClient.getDefaultOptions();

describe("ChartsAndFiltersPage", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { href: "", origin: window.location.origin });
    // A failed fetch would otherwise retry for seconds before the page shows it.
    queryClient.setDefaultOptions({
      queries: { ...defaultQueryOptions.queries, retry: false },
    });
  });

  afterEach(() => {
    queryClient.setDefaultOptions(defaultQueryOptions);
    vi.unstubAllGlobals();
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    fetchMock.clearHistory();
    queryClient.resetQueries();
  });

  it("renders step 6 and lists every closed, hybrid and demographic question", async () => {
    mockAnswers();
    await renderLoaded();

    expect(screen.getByText("Step 6 of 6")).toBeInTheDocument();
    expect(
      screen.getByText("Set up your charts and filters"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Your 1 closed, 1 hybrid and 2 demographic questions each become a chart or a filter on your dashboard. They are set up from the data in the file. Open each one to give it a short name.",
      ),
    ).toBeInTheDocument();
    expect(questionButton(1)).toHaveTextContent("Hybrid");
    expect(questionButton(7)).toHaveTextContent("Filter");
    expect(questionButton(3)).toHaveTextContent("Demographic");
    expect(
      screen.queryByRole("button", { name: /^Question 4\b/ }),
    ).not.toBeInTheDocument();
    await waitForAnswers();
    expect(questionButton(7)).toHaveTextContent("4 answers");
  });

  it("shows each question's short name and flags the ones without one", async () => {
    mockAnswers();
    await renderLoaded();

    expect(
      screen.getByRole("button", { name: /^Question 3 · Respondent type/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^Question 2 · needs a short name/ }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Needs a name")).toHaveLength(3);

    await expandQuestion(3);
    expect(screen.getByText("Respondent type")).toBeInTheDocument();
    await expandQuestion(2);
    expect(screen.getByText("Not named yet")).toBeInTheDocument();
  });

  it("saves the short name when the field loses focus", async () => {
    mockAnswers();
    mockRoute(updateMock("q2-uuid"));
    await renderLoaded();
    await expandQuestion(2);

    const field = screen.getByLabelText("Short name, used on the dashboard");
    await fireEvent.input(field, { target: { value: "Region" } });
    await fireEvent.focusOut(field);

    await waitFor(() => {
      expect(requests("PATCH")).toEqual([
        {
          url: expect.stringContaining("/questions/q2-uuid/"),
          body: { short_name: "Region" },
        },
      ]);
    });
  });

  it("fills the short name from the question wording", async () => {
    mockAnswers();
    mockRoute(updateMock("q2-uuid"));
    await renderLoaded();
    await expandQuestion(2);

    await fireEvent.click(
      screen.getByRole("button", { name: "Use the question" }),
    );

    await waitFor(() => {
      expect(requests("PATCH")).toEqual([
        {
          url: expect.stringContaining("/questions/q2-uuid/"),
          body: { short_name: "Which region are you responding from" },
        },
      ]);
    });
  });

  it("refuses a short name over 40 characters", async () => {
    mockAnswers();
    mockRoute(updateMock("q2-uuid"));
    await renderLoaded();
    await expandQuestion(2);

    const field = screen.getByLabelText("Short name, used on the dashboard");
    await fireEvent.input(field, { target: { value: "r".repeat(41) } });
    await fireEvent.focusOut(field);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "This is 41 characters. Keep it under 40 so it fits the dashboard.",
    );
    expect(requests("PATCH")).toEqual([]);
  });

  it("refuses a short name another question already uses", async () => {
    mockAnswers();
    mockRoute(updateMock("q2-uuid"));
    await renderLoaded();
    await expandQuestion(2);

    const field = screen.getByLabelText("Short name, used on the dashboard");
    await fireEvent.input(field, { target: { value: "respondent type" } });
    await fireEvent.focusOut(field);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Question 3 already uses this name. Two filters with the same label cannot be told apart.",
    );
    expect(requests("PATCH")).toEqual([]);
  });

  it("shows an error when the short name cannot be saved", async () => {
    mockAnswers();
    mockRoute(updateErrorMock("q2-uuid"));
    await renderLoaded();
    await expandQuestion(2);

    const field = screen.getByLabelText("Short name, used on the dashboard");
    await fireEvent.input(field, { target: { value: "Region" } });
    await fireEvent.focusOut(field);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "The name for question 2 was not saved. Try again.",
      );
    });
  });

  it("lets a closed question filter across all questions or show on its own", async () => {
    mockAnswers();
    mockRoute(updateMock("q7-uuid"));
    await renderLoaded();
    await expandQuestion(7);

    const group = screen.getByRole("group", {
      name: "How this question works",
    });
    expect(
      within(group).getByRole("radio", { name: /Filter across all questions/ }),
    ).toBeChecked();

    await fireEvent.click(
      within(group).getByRole("radio", { name: /Show on its own/ }),
    );

    await waitFor(() => {
      expect(requests("PATCH")).toEqual([
        {
          url: expect.stringContaining("/questions/q7-uuid/"),
          body: { dashboard_role: "standalone" },
        },
      ]);
    });
  });

  it("explains that a hybrid question filters its paired question", async () => {
    mockAnswers();
    await renderLoaded();
    await expandQuestion(1);

    expect(
      screen.getByText(
        "This is a hybrid question. It filters Q4 rather than the whole dashboard. To change that, edit the pairing on the previous step.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("group", { name: "How this question works" }),
    ).not.toBeInTheDocument();
  });

  it("says when every question is open", async () => {
    mockRoute({
      ...questionsMock,
      body: QUESTIONS.filter((question) => question.type === "open"),
    });
    render(ChartsAndFiltersPage, TEST_DATA);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Every question is open, so there are no charts or filters to set up.",
        ),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: /^Question/ }),
    ).not.toBeInTheDocument();
  });

  it("shows the answers ordered by count with their shares when a question is opened", async () => {
    mockAnswers();
    await renderLoaded();
    await waitForAnswers();

    await expandQuestion(2);

    expect(
      screen.getByText("Ordered by how often each answer was given."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "3 answers. If two of these are really the same answer, tick them and merge.",
      ),
    ).toBeInTheDocument();
    expect(answerRows()).toEqual([
      "England 3 (50%) Rename",
      "Scotland 2 (33%) Rename",
      "Wales 1 (17%)",
    ]);
    expect(screen.queryByText(/and \d+ more/)).not.toBeInTheDocument();
  });

  it("shows a scale in scale order instead of by count", async () => {
    mockAnswers(SCALE_ANSWERS);
    await renderLoaded();
    await waitFor(() => {
      expect(screen.getByText("5 answers")).toBeInTheDocument();
    });

    await expandQuestion(2);

    expect(
      screen.getByText(
        /These answers form a scale, so they're shown in scale order/,
      ),
    ).toBeInTheDocument();
    expect(answerNames()).toEqual([
      "Strongly agree",
      "Agree",
      "Neither agree nor disagree",
      "Disagree",
      "Strongly disagree",
    ]);
    expect(screen.getByText("and 2 more")).toBeInTheDocument();
  });

  it("keeps one-off answers after the scale, ordered by count", async () => {
    mockAnswers([
      ...SCALE_ANSWERS,
      { text: "Not sure", count: 2, responses: ["ns1", "ns2"] },
      { text: "N/A", count: 1, responses: ["na1"] },
    ]);
    await renderLoaded();
    await waitFor(() => {
      expect(screen.getByText("7 answers")).toBeInTheDocument();
    });

    await expandQuestion(2);

    expect(
      screen.getByText(
        /These answers form a scale, so they're shown in scale order/,
      ),
    ).toBeInTheDocument();
    expect(answerNames()).toEqual([
      "Strongly agree",
      "Agree",
      "Neither agree nor disagree",
      "Disagree",
      "Strongly disagree",
      "Not sure",
      "N/A",
    ]);
  });

  it("merges the ticked answers into one name and shows what it was grouped from", async () => {
    let current = RESPONDENT_ANSWERS;
    mockRoute(answersMock("q1-uuid", AGREEMENT_ANSWERS));
    mockRoute(answersMock("q2-uuid", REGION_ANSWERS));
    mockRoute(answersMock("q3-uuid", () => current));
    mockRoute(answersMock("q7-uuid", PENALTY_ANSWERS));
    mockRoute(mergeMock("q3-uuid"));
    await renderLoaded();
    await waitForAnswers();
    await expandQuestion(3);

    await fireEvent.click(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    );
    await fireEvent.click(
      screen.getByRole("checkbox", { name: "Select individual for merging" }),
    );
    await fireEvent.click(
      screen.getByRole("button", { name: "Merge selected (2)" }),
    );

    const nameInput = screen.getByLabelText(
      "Combine 2 answers into one, called",
    ) as HTMLInputElement;
    expect(nameInput.value).toBe("Individual");
    current = MERGED_RESPONDENT_ANSWERS;
    await fireEvent.click(screen.getByRole("button", { name: "Merge" }));

    await waitFor(() => {
      expect(requests("POST")).toEqual([
        {
          url: expect.stringContaining(
            "/questions/q3-uuid/demographics/merge/",
          ),
          body: { new_value: "Individual", responses: ["i1", "i2", "i3"] },
        },
      ]);
    });
    await waitFor(() => {
      expect(questionButton(3)).toHaveTextContent("2 answers");
    });
    expect(answerRows()).toEqual([
      "Individual grouped from Individual, individual 3 (60%) Rename",
      "Organisation 2 (40%) Rename",
    ]);
    expect(
      screen.getByText(
        "2 answers, grouped from 3 spellings. If two of these are really the same answer, tick them and merge.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Combine 2 answers into one, called"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    ).not.toBeChecked();
  });

  it("only allows a merge once two answers are ticked and can clear the selection", async () => {
    mockAnswers();
    await renderLoaded();
    await waitForAnswers();
    await expandQuestion(3);

    expect(
      screen.getByRole("button", { name: "Merge selected" }),
    ).toBeDisabled();
    expect(
      screen.getByText("Tick two or more answers to merge them"),
    ).toBeInTheDocument();

    await fireEvent.click(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    );
    expect(
      screen.getByRole("button", { name: "Merge selected (1)" }),
    ).toBeDisabled();

    await fireEvent.click(
      screen.getByRole("button", { name: "Clear selection" }),
    );
    expect(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    ).not.toBeChecked();
    expect(
      screen.getByText("Tick two or more answers to merge them"),
    ).toBeInTheDocument();
  });

  it("renames an answer by merging its responses under the new name", async () => {
    mockAnswers();
    mockRoute(mergeMock("q3-uuid"));
    await renderLoaded();
    await waitForAnswers();
    await expandQuestion(3);

    expect(
      screen.queryByRole("button", { name: "Rename individual" }),
    ).not.toBeInTheDocument();
    await fireEvent.click(
      screen.getByRole("button", { name: "Rename Individual" }),
    );
    const input = screen.getByLabelText(
      "New name for Individual",
    ) as HTMLInputElement;
    expect(input.value).toBe("Individual");
    await fireEvent.input(input, { target: { value: "Person" } });
    await fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(requests("POST")).toEqual([
        {
          url: expect.stringContaining(
            "/questions/q3-uuid/demographics/merge/",
          ),
          body: { new_value: "Person", responses: ["i1", "i2"] },
        },
      ]);
    });
  });

  it("shows an error and keeps the selection when a merge fails", async () => {
    mockAnswers();
    mockRoute(mergeErrorMock("q3-uuid"));
    await renderLoaded();
    await waitForAnswers();
    await expandQuestion(3);
    await fireEvent.click(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    );
    await fireEvent.click(
      screen.getByRole("checkbox", { name: "Select individual for merging" }),
    );
    await fireEvent.click(
      screen.getByRole("button", { name: "Merge selected (2)" }),
    );

    await fireEvent.click(screen.getByRole("button", { name: "Merge" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "The answers for question 3 were not merged. Try again.",
      );
    });
    expect(
      screen.getByRole("checkbox", { name: "Select Individual for merging" }),
    ).toBeChecked();
    expect(
      screen.getByRole("checkbox", { name: "Select individual for merging" }),
    ).toBeChecked();
  });

  it("offers to try again when the answers cannot be loaded", async () => {
    mockRoute(answersMock("q1-uuid", AGREEMENT_ANSWERS));
    mockRoute(answersErrorMock("q2-uuid"));
    mockRoute(answersMock("q3-uuid", RESPONDENT_ANSWERS));
    mockRoute(answersMock("q7-uuid", PENALTY_ANSWERS));
    await renderLoaded();
    await waitFor(() => {
      expect(questionButton(2)).toHaveTextContent("Answers unavailable");
    });

    await expandQuestion(2);

    expect(
      screen.getByText("The answers could not be loaded."),
    ).toBeInTheDocument();
    const answerCalls = () =>
      fetchMock.callHistory
        .calls()
        .filter((call) => call.url.includes("/questions/q2-uuid/demographics/"))
        .length;
    const before = answerCalls();
    await fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => {
      expect(answerCalls()).toBe(before + 1);
    });
  });

  it("shows an error when the questions cannot be loaded", async () => {
    mockRoute(questionsErrorMock);
    render(ChartsAndFiltersPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Failed to load questions.")).toBeInTheDocument();
    });
  });

  it("blocks finishing until every closed question has a short name", async () => {
    mockAnswers();
    await renderLoaded();

    await fireEvent.click(
      screen.getByRole("button", { name: "Finish set-up" }),
    );

    const [summary] = screen.getAllByRole("alert");
    expect(summary).toHaveTextContent("There is a problem");
    expect(summary).toHaveTextContent(
      "Question 7: Enter a short name. This is what labels the filter on your dashboard.",
    );
    expect(summary).not.toHaveTextContent("Question 1");
    expect(screen.getByRole("link", { name: /^Question 7:/ })).toHaveAttribute(
      "href",
      "#short-name-q7-uuid",
    );
    const field = screen.getByLabelText("Short name, used on the dashboard");
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(field).toHaveAccessibleDescription(
      "Enter a short name. This is what labels the filter on your dashboard.",
    );
    expect(window.location.href).toBe("");
  });

  it("goes back to review questions and on to finish set-up once the closed questions are named", async () => {
    mockAnswers();
    await renderLoaded(withShortName("q7-uuid", "Penalties"));

    expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}/data-upload/review-questions`,
    );

    await fireEvent.click(
      screen.getByRole("button", { name: "Finish set-up" }),
    );
    expect(window.location.href).toBe(
      `/consultations/${CONSULTATION_ID}/data-upload/finalise`,
    );
  });

  it("matches snapshot", async () => {
    mockAnswers();
    const { container } = await renderLoaded();
    await waitForAnswers();
    await expandQuestion(2);
    expect(
      screen.getByText("Ordered by how often each answer was given."),
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });
});
