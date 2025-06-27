import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import QuestionTitle from './question-title.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/QuestionDetail/QuestionTitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-question-title
        .status=${args.status}
        .title=${args.title}
        .department=${args.department}
        .numResponses=${args.numResponses}
      ></iai-silver-question-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    status: "Open",
    title: "Q1: What regulatory frameworks should be established to govern AI systems in critical sectors such as healthcare, finance, and transportation?",
    department: "Chapter: Regulatory & Privacy Foundations",
    numResponses: 7000,
  },
};
