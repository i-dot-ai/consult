import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import DemographicsCard from './demographics-card.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/QuestionDetail/DemographicsCard',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-demographics-card
        .title=${args.title}  
        .data=${args.data}
      ></iai-demographics-card>
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
