import { html } from 'lit';

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
const TEST_MULTI_CHOICE_ANSWERS = ["answer 1", "answer 2"];

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Response',
  tags: ['autodocs'],
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
    free_text_answer_text: "Test free text answer.",
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "",
    evidenceRich: true,
  }
};

export const WithoutMultiChoice = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: "Test free text answer.",
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: false,
    multiple_choice_answer: undefined,
    searchValue: "",
    evidenceRich: true,
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
  }
};

export const WithSearchHighlight = {
  args: {
    id: "test-response",
    identifier: "test-response",
    individual: "test-individual",
    sentiment_position: "UNCLEAR",
    free_text_answer_text: "Test free text answer.",
    demographic_data: undefined,
    themes: TEST_THEMES,
    has_multiple_choice_question_part: true,
    multiple_choice_answer: TEST_MULTI_CHOICE_ANSWERS,
    searchValue: "free text",
    evidenceRich: true,
  }
};