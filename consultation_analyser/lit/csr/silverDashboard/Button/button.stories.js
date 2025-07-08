import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import Button from './button.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/Button',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-button
        .text=${args.text}
        .handleClick=${args.handleClick}
      ></iai-silver-button>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    text: "Test Button",
    handleClick: () => action("Button clicked")(event.target),
  },
};
