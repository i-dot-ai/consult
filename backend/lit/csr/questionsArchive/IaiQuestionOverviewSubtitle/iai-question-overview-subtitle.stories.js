import { html } from 'lit';

import IaiQuestionOverviewSubtitle from './iai-question-overview-subtitle.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/QuestionOverviewSubtitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-overview-subtitle
        .title=${args.title}
        .total=${args.total}
      ></iai-question-overview-subtitle>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    total: 100,
  },
};

export const EmptyLabel = {
  args: {
    title: "",
    total: 100,
  },
};

export const ZeroTotal = {
  args: {
    title: "Test Title",
    total: 0,
  },
};
