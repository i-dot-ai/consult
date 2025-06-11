import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiQuestionOverview from './iai-question-overview.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionOverview',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-overview
        .title=${args.title}
        .body=${args.body}
        .responses=${args.responses}
        .multiResponses=${args.multiResponses}
        .handleClose=${args.handleClose}
      ></iai-question-overview>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Question",
    body: "This is a test question".repeat(10),
    responses: {
      agreement: true,
      disagreement: true,
      unclear: true,
    },
    multiResponses: {
      "one": 10,
      "two": 20,
    },
    handleClose: action("Close button clicked"),
  },
};

export const WithoutFreetextResponses = {
  args: {
    title: "Test Question",
    body: "This is a test question".repeat(10),
    responses: {},
    multiResponses: {
      "one": 10,
      "two": 20,
    },
    handleClose: action("Close button clicked"),
  },
};

export const WithoutMultiResponses = {
  args: {
    title: "Test Question",
    body: "This is a test question".repeat(10),
    responses: {
      agreement: true,
      disagreement: true,
      unclear: true,
    },
    multiResponses: {},
    handleClose: action("Close button clicked"),
  },
};

export const WithoutAnyResponses = {
  args: {
    title: "Test Question",
    body: "This is a test question".repeat(10),
    responses: {},
    multiResponses: {},
    handleClose: action("Close button clicked"),
  },
};