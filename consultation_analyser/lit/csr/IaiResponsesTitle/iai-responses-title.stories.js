import { html } from 'lit';

import IaiResponsesTitle from './iai-responses-title.lit.csr.mjs';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponsesTitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-responses-title
        .total=${args.total}
      ></iai-responses-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    total: 100,
  },
};

export const ZeroTotal = {
  args: {
    total: 0,
  },
};

export const LargeTotal = {
  args: {
    total: 100000,
  },
};

export const NegativeTotal = {
  args: {
    total: -10,
  },
};