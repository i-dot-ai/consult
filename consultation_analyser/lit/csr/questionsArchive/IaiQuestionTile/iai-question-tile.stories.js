import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiQuestionTile from './iai-question-tile.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionTile',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-tile
        .questionId=${args.questionId}
        .title=${args.title}
        .body=${args.body}
        .maxLength=${args.maxLength}
        .highlighted=${args.highlighted}
        .searchValue=${args.searchValue}
        .handleViewClick=${args.handleViewClick}
        .handleBodyClick=${args.handleBodyClick}
        .handleFavouriteClick=${args.handleFavouriteClick}
      ></iai-question-tile>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    questionId: "test-question",
    title: "Test Question",
    body: "This is a test question".repeat(10),
    maxLength: 100,
    highlighted: "",
    searchValue: "",
    handleViewClick: action("View button clicked"),
  },
};

export const LongBody = {
  args: {
    questionId: "test-question",
    title: "Test Question",
    body: "This is a test question".repeat(100),
    maxLength: 500,
    highlighted: "",
    searchValue: "",
    handleViewClick: action("View button clicked"),
  },
};

export const WithClickHandlers = {
  args: {
    questionId: "test-question",
    title: "Test Question",
    body: "This is a test question".repeat(10),
    maxLength: 100,
    highlighted: "",
    searchValue: "",
    handleViewClick: action("View button clicked"),
    handleFavouriteClick: action("Favourite button clicked"),
    handleBodyClick: action("Body clicked"),
  },
};