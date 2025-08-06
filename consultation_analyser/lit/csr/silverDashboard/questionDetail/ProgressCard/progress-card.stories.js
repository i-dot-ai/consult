import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import ProgressCard from './progress-card.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/QuestionDetail/ProgressCard',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-progress-card
        .title=${args.title}  
        .data=${args.data}
      ></iai-progress-card>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Card",
    data: {
      "Foo": 20,
      "Bar": 70,
      "Baz": 10,
    }
  },
};

export const NoTitle = {
  args: {
    title: "",
    data: {
      "Foo": 20,
      "Bar": 70,
      "Baz": 10,
    }
  },
};