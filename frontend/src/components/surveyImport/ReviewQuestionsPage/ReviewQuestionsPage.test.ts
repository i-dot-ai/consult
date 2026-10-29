import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import ReviewQuestionsPage from "./ReviewQuestionsPage.svelte";
import {
  CONSULTATION_ID,
  MANY_QUESTIONS,
  QUESTIONS,
  answersMock,
  questionsMock,
  updateErrorMock,
  updateMock,
} from "./mocks";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

const TEST_DATA = { consultationId: CONSULTATION_ID };

async function renderLoaded(questions = QUESTIONS) {
  mockRoute({ ...questionsMock, body: questions });
  const view = render(ReviewQuestionsPage, TEST_DATA);
  await waitFor(() => {
    expect(screen.getByText(questions[0].text)).toBeInTheDocument();
  });
  return view;
}

function typeSelect(number: number) {
  return screen.getAllByLabelText("This question is")[
    number - 1
  ] as HTMLSelectElement;
}

function patchCalls() {
  return fetchMock.callHistory
    .calls()
    .filter((call) => (call.options.method ?? "").toUpperCase() === "PATCH")
    .map((call) => ({
      url: call.url,
      body: JSON.parse(call.options.body as string),
    }));
}

describe("ReviewQuestionsPage", () => {
  beforeEach(() => {
    vi.stubGlobal("location", { href: "", origin: window.location.origin });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    fetchMock.clearHistory();
    queryClient.resetQueries();
  });

  it("renders step 5 and lists every question in file order", async () => {
    await renderLoaded();

    expect(screen.getByText("Step 5 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Review your questions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("6 questions · 3 open · 1 closed · 1 hybrid"),
    ).toBeInTheDocument();
    expect(screen.getByText("Nothing changed yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Every change made here is tracked/),
    ).toBeInTheDocument();
    const rows = screen.getAllByText(/^Q\d$/).map((el) => el.textContent);
    expect(rows).toEqual(["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]);
  });

  it("offers open, closed, hybrid and demographic", async () => {
    await renderLoaded();

    const labels = Array.from(typeSelect(3).options).map(
      (option) => option.textContent,
    );
    expect(labels).toEqual([
      "Choose a type",
      "Open",
      "Closed",
      "Hybrid",
      "Demographic",
    ]);
  });

  it("shows hybrid on the closed question, with the open question it is paired with", async () => {
    await renderLoaded();

    expect(typeSelect(1).value).toBe("hybrid");
    expect(
      screen.getByText(
        /Explains Q2\. Its answers can be filtered by this one\./,
      ),
    ).toBeInTheDocument();
    expect(typeSelect(2).value).toBe("open");
    expect(typeSelect(3).value).toBe("");
  });

  it("saves a chosen type through the v2 question endpoint", async () => {
    await renderLoaded();
    mockRoute(
      updateMock("q3-uuid", { type: "demographic", status: "configured" }),
    );

    await fireEvent.change(typeSelect(3), { target: { value: "demographic" } });

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining(
            `/api/v2/consultations/${CONSULTATION_ID}/questions/q3-uuid/`,
          ),
          body: { type: "demographic", closed_question: null },
        },
      ]);
    });
  });

  it("choosing hybrid on a closed question asks which open question explains it, then links that question", async () => {
    await renderLoaded(
      QUESTIONS.map((question) =>
        question.id === "q2-uuid"
          ? { ...question, closed_question: null }
          : question,
      ),
    );
    mockRoute(
      updateMock("q4-uuid", { type: "open", closed_question: "q1-uuid" }),
    );

    await fireEvent.change(typeSelect(1), { target: { value: "hybrid" } });

    const linkSelect = screen.getByLabelText(
      "Question to link to",
    ) as HTMLSelectElement;
    expect(
      Array.from(linkSelect.options).map((option) => option.textContent),
    ).toEqual([
      "Choose an open question",
      `Q2 ${QUESTIONS[1].text}`,
      `Q4 ${QUESTIONS[3].text}`,
      `Q6 ${QUESTIONS[5].text}`,
    ]);
    const linkButton = screen.getByRole("button", { name: "Link" });
    expect(linkButton).toBeDisabled();

    await fireEvent.change(linkSelect, { target: { value: "q4-uuid" } });
    expect(linkButton).not.toBeDisabled();
    expect(patchCalls()).toEqual([]);

    await fireEvent.click(linkButton);

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q4-uuid/"),
          body: { type: "open", closed_question: "q1-uuid" },
        },
      ]);
    });
  });

  it("cancelling the link picker saves nothing and closes it", async () => {
    await renderLoaded(
      QUESTIONS.map((question) =>
        question.id === "q2-uuid"
          ? { ...question, closed_question: null }
          : question,
      ),
    );

    await fireEvent.change(typeSelect(1), { target: { value: "hybrid" } });
    await fireEvent.change(screen.getByLabelText("Question to link to"), {
      target: { value: "q4-uuid" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(
      screen.queryByLabelText("Question to link to"),
    ).not.toBeInTheDocument();
    expect(patchCalls()).toEqual([]);
    expect(typeSelect(1).value).toBe("closed");
  });

  it("saving another row leaves an open link picker and an open edit in place", async () => {
    await renderLoaded();
    mockRoute(updateMock("q3-uuid", { type: "demographic" }));

    await fireEvent.change(typeSelect(5), { target: { value: "hybrid" } });
    await fireEvent.click(
      screen.getByRole("button", { name: "Edit wording of question 4" }),
    );
    await fireEvent.change(typeSelect(3), { target: { value: "demographic" } });
    await waitFor(() => {
      expect(patchCalls()).toHaveLength(1);
      expect(typeSelect(3)).not.toBeDisabled();
    });

    expect(screen.getByLabelText("Question to link to")).toBeInTheDocument();
    expect(typeSelect(5).value).toBe("hybrid");
    expect(screen.getByLabelText("Question wording")).toBeInTheDocument();

    const pickerCancel = within(
      screen.getByRole("group", {
        name: "Link question 5 to an open question",
      }),
    ).getByRole("button", { name: "Cancel" });
    await fireEvent.click(pickerCancel);
    expect(
      screen.queryByLabelText("Question to link to"),
    ).not.toBeInTheDocument();
    expect(typeSelect(5).value).toBe("closed");
    expect(screen.getByLabelText("Question wording")).toBeInTheDocument();
  });

  it("choosing hybrid on an unset question makes it closed first", async () => {
    await renderLoaded();
    mockRoute(updateMock("q3-uuid", { type: "closed" }));

    await fireEvent.change(typeSelect(3), { target: { value: "hybrid" } });

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q3-uuid/"),
          body: { type: "closed", closed_question: null },
        },
      ]);
    });
  });

  it("removing the link sets the pair back to a plain closed question", async () => {
    await renderLoaded();
    mockRoute(updateMock("q2-uuid", { closed_question: null }));

    await fireEvent.click(
      screen.getByRole("button", { name: "Remove link to Q2" }),
    );

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q2-uuid/"),
          body: { closed_question: null },
        },
      ]);
    });
  });

  it("changing a hybrid question to another type clears the link", async () => {
    await renderLoaded();
    mockRoute(updateMock("q2-uuid", { closed_question: null }));
    mockRoute(updateMock("q1-uuid", { type: "open" }));

    await fireEvent.change(typeSelect(1), { target: { value: "open" } });

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q1-uuid/"),
          body: { type: "open", closed_question: null },
        },
      ]);
    });
  });

  it("changing a hybrid question back to closed clears the link without retyping it", async () => {
    await renderLoaded();
    mockRoute(updateMock("q2-uuid", { closed_question: null }));

    await fireEvent.change(typeSelect(1), { target: { value: "closed" } });

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q2-uuid/"),
          body: { closed_question: null },
        },
      ]);
    });
  });

  it("stops unlinking a hybrid question's pairs after the first failed save", async () => {
    const twoLinks = QUESTIONS.map((question) =>
      question.id === "q4-uuid"
        ? { ...question, closed_question: "q1-uuid" }
        : question,
    );
    await renderLoaded(twoLinks);
    mockRoute(updateErrorMock("q2-uuid"));
    mockRoute(updateMock("q4-uuid", { closed_question: null }));

    await fireEvent.change(typeSelect(1), { target: { value: "closed" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Question 2 was not saved.",
      );
    });
    expect(patchCalls()).toEqual([
      {
        url: expect.stringContaining("/questions/q2-uuid/"),
        body: { closed_question: null },
      },
    ]);
    expect(typeSelect(1).value).toBe("hybrid");
    expect(typeSelect(1)).not.toBeDisabled();
  });

  it("explains that an open question is needed before a hybrid link", async () => {
    await renderLoaded(
      QUESTIONS.map((question) =>
        question.id === "q1-uuid"
          ? question
          : { ...question, type: null, closed_question: null },
      ),
    );

    await fireEvent.change(typeSelect(1), { target: { value: "hybrid" } });

    expect(
      screen.getByText("Set an open question first, then link it to this one."),
    ).toBeInTheDocument();
  });

  it("shows an error and keeps the page when saving fails", async () => {
    await renderLoaded();
    mockRoute(updateErrorMock("q3-uuid"));

    await fireEvent.change(typeSelect(3), { target: { value: "closed" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Question 3 was not saved. Try again.",
      );
    });
    expect(typeSelect(3)).not.toBeDisabled();
    expect(typeSelect(3).value).toBe("");
  });

  it("does not open the link picker when making the question closed fails", async () => {
    await renderLoaded();
    mockRoute(updateErrorMock("q3-uuid"));

    await fireEvent.change(typeSelect(3), { target: { value: "hybrid" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Question 3 was not saved.",
      );
    });
    expect(
      screen.queryByLabelText("Question to link to"),
    ).not.toBeInTheDocument();
    expect(typeSelect(3).value).toBe("");
  });

  it("shows a sample of answers on request", async () => {
    await renderLoaded();
    mockRoute(answersMock("q4-uuid", ["Cost", "Design", "Durability"]));

    expect(screen.queryByText("Cost")).not.toBeInTheDocument();
    await fireEvent.click(screen.getAllByText("Show answers")[3]);

    await waitFor(() => {
      expect(screen.getByText("Cost")).toBeInTheDocument();
    });
    expect(
      screen.getByText("A sample. 3 of 380 answers to this question"),
    ).toBeInTheDocument();
    const sampleCall = fetchMock.callHistory
      .calls()
      .find((call) => call.url.includes("/questions/q4-uuid/responses/"));
    expect(sampleCall?.url).toContain("page_size=3");

    await fireEvent.click(screen.getByText("Hide answers"));
    expect(screen.queryByText("Cost")).not.toBeInTheDocument();
  });

  it("says there are no answers when the sample cannot be loaded", async () => {
    await renderLoaded();
    mockRoute({ ...answersMock("q4-uuid", []), status: 500 });

    await fireEvent.click(screen.getAllByText("Show answers")[3]);

    await waitFor(() => {
      expect(
        screen.getByText("No answers for this question."),
      ).toBeInTheDocument();
    });
  });

  it("edits the wording and saves it through the v2 question endpoint", async () => {
    await renderLoaded();
    mockRoute(updateMock("q3-uuid", { text: "Which region are you in?" }));

    await fireEvent.click(
      screen.getByRole("button", { name: "Edit wording of question 3" }),
    );
    const box = screen.getByLabelText(
      "Question wording",
    ) as HTMLTextAreaElement;
    expect(box.value).toBe(QUESTIONS[2].text);

    await fireEvent.input(box, {
      target: { value: "Which region are you in?" },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Save wording" }));

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q3-uuid/"),
          body: { text: "Which region are you in?" },
        },
      ]);
    });
  });

  it("rejects empty wording and cancels an edit without saving", async () => {
    await renderLoaded();

    await fireEvent.click(
      screen.getByRole("button", { name: "Edit wording of question 3" }),
    );
    const box = screen.getByLabelText("Question wording");
    await fireEvent.input(box, { target: { value: "   " } });
    await fireEvent.click(screen.getByRole("button", { name: "Save wording" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Enter the question wording. It cannot be empty.",
    );
    expect(patchCalls()).toEqual([]);

    await fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByLabelText("Question wording")).not.toBeInTheDocument();
    expect(screen.getByText(QUESTIONS[2].text)).toBeInTheDocument();
    expect(patchCalls()).toEqual([]);
  });

  it("proposes a hybrid pair when an explaining open question follows a closed one", async () => {
    await renderLoaded();
    mockRoute(
      updateMock("q6-uuid", { type: "open", closed_question: "q5-uuid" }),
    );

    expect(
      screen.getByText(
        "This looks like a hybrid pair. Q6 asks people to explain this answer, so its answers could be read by how people answered here.",
      ),
    ).toBeInTheDocument();

    await fireEvent.click(
      screen.getByRole("button", { name: "Yes, they are a pair" }),
    );

    await waitFor(() => {
      expect(patchCalls()).toEqual([
        {
          url: expect.stringContaining("/questions/q6-uuid/"),
          body: { type: "open", closed_question: "q5-uuid" },
        },
      ]);
    });
  });

  it("rejecting a proposed pair hides it without saving", async () => {
    await renderLoaded();

    await fireEvent.click(
      screen.getByRole("button", { name: "No, separate questions" }),
    );

    expect(
      screen.queryByText(/This looks like a hybrid pair/),
    ).not.toBeInTheDocument();
    expect(patchCalls()).toEqual([]);
    expect(
      screen.getAllByRole("button", { name: "This question explains another" }),
    ).toHaveLength(1);
  });

  it("only proposes an unlinked pair", async () => {
    await renderLoaded();

    const proposals = screen.getAllByText(/This looks like a hybrid pair/);
    expect(proposals).toHaveLength(1);
    expect(proposals[0]).toHaveTextContent("Q6 asks people to explain");
  });

  it("counts changes made on the page and can sort them first", async () => {
    await renderLoaded();
    mockRoute(
      updateMock("q3-uuid", { type: "demographic", status: "configured" }),
    );
    const sort = screen.getByLabelText("Sort") as HTMLSelectElement;
    expect(
      Array.from(sort.options).map((option) => option.textContent),
    ).toEqual(["File order", "Changed first"]);

    await fireEvent.change(typeSelect(3), { target: { value: "demographic" } });
    await waitFor(() => {
      expect(
        screen.getByText("1 question changed in total"),
      ).toBeInTheDocument();
    });
    expect(screen.getAllByText(/^Q\d$/)[0]).toHaveTextContent("Q1");

    await fireEvent.change(sort, { target: { value: "changed" } });
    expect(screen.getAllByText(/^Q\d$/).map((el) => el.textContent)).toEqual([
      "Q3",
      "Q1",
      "Q2",
      "Q4",
      "Q5",
      "Q6",
    ]);

    await fireEvent.change(sort, { target: { value: "file" } });
    expect(screen.getAllByText(/^Q\d$/)[0]).toHaveTextContent("Q1");
  });

  it("tags a changed row with what changed", async () => {
    let current = QUESTIONS;
    mockRoute({ ...questionsMock, body: () => current });
    render(ReviewQuestionsPage, TEST_DATA);
    await waitFor(() => {
      expect(screen.getByText(QUESTIONS[0].text)).toBeInTheDocument();
    });
    mockRoute(
      updateMock("q6-uuid", { type: "open", closed_question: "q5-uuid" }),
    );
    mockRoute(
      updateMock("q3-uuid", { type: "demographic", status: "configured" }),
    );

    current = QUESTIONS.map((question) =>
      question.id === "q6-uuid"
        ? { ...question, closed_question: "q5-uuid" }
        : question,
    );
    await fireEvent.click(
      screen.getByRole("button", { name: "Yes, they are a pair" }),
    );
    await waitFor(() => {
      expect(screen.getByText("Set to hybrid")).toBeInTheDocument();
    });
    expect(screen.getByText("Linked")).toBeInTheDocument();
    expect(screen.getByText("1 question changed in total")).toBeInTheDocument();

    mockRoute(updateMock("q6-uuid", { closed_question: null }));
    current = QUESTIONS;
    await fireEvent.click(
      screen.getByRole("button", { name: "Remove link to Q6" }),
    );
    await waitFor(() => {
      expect(screen.queryByText("Linked")).not.toBeInTheDocument();
    });
    expect(screen.queryByText("Set to hybrid")).not.toBeInTheDocument();
    expect(screen.queryByText("Changed")).not.toBeInTheDocument();
    expect(screen.getByText("1 question changed in total")).toBeInTheDocument();

    current = current.map((question) =>
      question.id === "q3-uuid"
        ? { ...question, type: "demographic" }
        : question,
    );
    await fireEvent.change(typeSelect(3), { target: { value: "demographic" } });
    await waitFor(() => {
      expect(screen.getByText("Set to demographic")).toBeInTheDocument();
    });
    expect(screen.queryByText("Wording edited")).not.toBeInTheDocument();
  });

  it("does not count a failed save as a change", async () => {
    await renderLoaded();
    mockRoute(updateErrorMock("q3-uuid"));

    await fireEvent.change(typeSelect(3), { target: { value: "closed" } });
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("was not saved");
    });

    expect(screen.getByText("Nothing changed yet")).toBeInTheDocument();
    expect(screen.queryByText(/^Set to/)).not.toBeInTheDocument();
  });

  it("tags a hybrid question retyped to open on its own row", async () => {
    let current = QUESTIONS;
    mockRoute({ ...questionsMock, body: () => current });
    render(ReviewQuestionsPage, TEST_DATA);
    await waitFor(() => {
      expect(screen.getByText(QUESTIONS[0].text)).toBeInTheDocument();
    });
    mockRoute(updateMock("q1-uuid", { type: "open" }));
    current = QUESTIONS.map((question) =>
      question.id === "q1-uuid"
        ? { ...question, type: "open" }
        : question.id === "q2-uuid"
          ? { ...question, closed_question: null }
          : question,
    );

    await fireEvent.change(typeSelect(1), { target: { value: "open" } });

    await waitFor(() => {
      expect(screen.getByText("Set to open")).toBeInTheDocument();
    });
    expect(screen.getByText("1 question changed in total")).toBeInTheDocument();
  });

  it("tags a linked open question retyped to demographic on its own row", async () => {
    let current = QUESTIONS;
    mockRoute({ ...questionsMock, body: () => current });
    render(ReviewQuestionsPage, TEST_DATA);
    await waitFor(() => {
      expect(screen.getByText(QUESTIONS[0].text)).toBeInTheDocument();
    });
    mockRoute(
      updateMock("q2-uuid", { type: "demographic", closed_question: null }),
    );
    current = QUESTIONS.map((question) =>
      question.id === "q2-uuid"
        ? { ...question, type: "demographic", closed_question: null }
        : question,
    );

    await fireEvent.change(typeSelect(2), { target: { value: "demographic" } });

    await waitFor(() => {
      expect(screen.getByText("Set to demographic")).toBeInTheDocument();
    });
    expect(screen.getByText("1 question changed in total")).toBeInTheDocument();
    expect(typeSelect(1).value).toBe("closed");
    expect(screen.queryByText("Set to closed")).not.toBeInTheDocument();
  });

  it("pages at 10 questions and lets the page size change", async () => {
    await renderLoaded(MANY_QUESTIONS);

    expect(screen.getByText("Showing 1 to 10 of 12")).toBeInTheDocument();
    expect(screen.queryByText("Question 11")).not.toBeInTheDocument();

    await fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(screen.getByText("Showing 11 to 12 of 12")).toBeInTheDocument();
    expect(screen.getByText("Question 11")).toBeInTheDocument();

    await fireEvent.change(screen.getByLabelText("Per page"), {
      target: { value: "20" },
    });
    expect(screen.getByText("Showing 1 to 12 of 12")).toBeInTheDocument();
  });

  it("hides the pager at 10 questions or fewer", async () => {
    await renderLoaded();

    expect(screen.queryByText(/^Showing/)).not.toBeInTheDocument();
  });

  it("blocks continuing when no question is open", async () => {
    await renderLoaded(
      QUESTIONS.map((question) => ({
        ...question,
        type: "closed",
        closed_question: null,
      })),
    );

    await fireEvent.click(
      screen.getByRole("button", { name: "Continue to closed questions" }),
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "No question is set to open, so there will be no themes to sign off.",
    );
    expect(window.location.href).toBe("");
  });

  it("goes back to delete questions and on to closed questions", async () => {
    await renderLoaded();

    expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}/data-upload/delete-questions`,
    );

    await fireEvent.click(
      screen.getByRole("button", { name: "Continue to closed questions" }),
    );
    expect(window.location.href).toBe(
      `/consultations/${CONSULTATION_ID}/data-upload/charts-and-filters`,
    );
  });

  it("matches snapshot", async () => {
    const { container } = await renderLoaded();

    expect(container).toMatchSnapshot();
  });
});
