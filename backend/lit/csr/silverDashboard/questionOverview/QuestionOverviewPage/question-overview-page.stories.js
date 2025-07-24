import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import QuestionOverviewPage from './question-overview-page.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/QuestionOverview/QuestionOverviewPage',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-question-overview-page
      ></iai-question-overview-page>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
  },
};
