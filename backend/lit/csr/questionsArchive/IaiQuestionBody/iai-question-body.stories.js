import { html } from 'lit';

import IaiQuestionBody from './iai-question-body.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionBody',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-body
        .text=${args.text}
        .searchValue=${args.searchValue}
      ></iai-question-body>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    text: "Test question body",
  },
};

export const WithHighlight = {
  args: {
    text: "Test question body with highlighted text",
    searchValue: "highlighted text",
  },
};
