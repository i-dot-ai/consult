import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiAnimatedNumber from './iai-animated-number.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/AnimatedNumber',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-animated-number
        .number=${args.number}
        .duration=${args.duration /* milliseconds */}
      ></iai-animated-number>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    number: 100,
    duration: 2000,
  },
};

export const LongDuration = {
  args: {
    number: 100,
    duration: 10000,
  },
};

export const ShortDuration = {
  args: {
    number: 100,
    duration: 100,
  },
};

export const Float = {
  args: {
    number: 90.25,
    duration: 500.25,
  },
};