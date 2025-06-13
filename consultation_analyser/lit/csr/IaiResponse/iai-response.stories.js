import { html } from 'lit';

import { expect, within } from '@storybook/test';

import IaiResponse from './iai-response.lit.csr.mjs';

const TEST_THEMES = [
  {
    name: "theme 1",
    description: "description 1"
  },
  {
    name: "theme 2",
    description: "description 2"
  }
];
const TEST_FREE_TEXT_ANSWER = "Test free text answer.";
const TEST_MULTI_CHOICE_ANSWERS = ["answer 1", "answer 2"];

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponsesDashboard/Response',
  tags: ['autodocs'],
  argTypes: {
    sentiment_position: {
      control: { type: "select" },
      options: [
        "AGREEMENT",
        "DISAGREEMENT",
        "UNCLEAR",
      ]
    }
  },
  render: (args) => {
    return html`
      <iai-response
        .id=${args.inputId}
        .identifier=${args.identifier}
        .individual=${args.individual}
        .sentiment_position=${args.sentiment_position}
        .free_text_answer_text=${args.free_text_answer_text}
        .demographic_data=${args.demographic_data}
        .themes=${args.themes}
        .has_multiple_choice_question_part=${args.has_multiple_choice_question_part}
        .multiple_choice_answer=${args.multiple_choice_answer}
        .searchValue=${args.searchValue}
        .evidenceRich=${args.evidenceRich}
        .skeleton=${args.skeleton}
      ></iai-response>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args

export const Default = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const multiChoiceTitle = canvas.queryByText("Response to multiple choice");
    expect(multiChoiceTitle).toBeInTheDocument();

    const freeTextAnswer = canvas.getByTestId("free-text-answer");
    expect(freeTextAnswer).toBeInTheDocument();

    const multiChoiceAnswers = canvas.getByText(TEST_MULTI_CHOICE_ANSWERS.join(", "));
    expect(multiChoiceAnswers).toBeInTheDocument();
  }
};

export const WithoutMultiChoice = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: false,
    multiple_choice_answer: undefined,
    searchValue: "",
    evidenceRich: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const multiChoiceTitle = canvas.queryByText("Response to multiple choice");
    expect(multiChoiceTitle).toBe(null);
  }
};

export const WithoutFreeText = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: undefined,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const freeTextAnswer = canvas.queryByTestId("free-text-answer");
    expect(freeTextAnswer).toBe(null);
  }
};

export const WithSearchHighlight = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "free text",
    evidenceRich: true,
  },
  play: async ({ canvasElement }) => {
    const highlightedText = canvasElement.querySelector(".matched-text");
    expect(highlightedText.innerText).toBe("free text");
  }
};

export const NotEvidenceRich = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: false,
  }
};

export const Agreement = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "AGREEMENT",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: false,
  }
};

export const Disagreement = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "DISAGREEMENT",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER,
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: false,
  }
};

export const Skeleton = {
  args: {
    id: "skeleton-response",
    identifier: "skeleton-response",
    individual: "skeleton-individual",
    free_text_answer_text: TEST_FREE_TEXT_ANSWER.repeat(5),
    skeleton: true,
  }
};