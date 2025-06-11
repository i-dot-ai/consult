import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiQuestionTiles from './iai-question-tiles.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionTiles',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-tiles
        .consultationName=${args.consultationName}
        .questions=${args.questions}
      ></iai-question-tiles>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    consultationName: "test-question",
    questions: [...Array(10).keys()].map(n => ({
      id: `question-${n}`,
      url: `/questions/question-${n}`,
      title: `Question ${n}`,
      body: "This is a test question".repeat(10),
      responses: {},
      multiResponses: {},
    }))
  },
};

export const EmptyQuestions = {
  args: {
    consultationName: "test-question",
    questions: [],
  },
};
