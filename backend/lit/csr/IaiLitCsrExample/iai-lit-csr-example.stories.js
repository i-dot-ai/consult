import { html } from 'lit';

import IaiLitCsrExample from './iai-lit-csr-example.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Examples/IaiLitCsrExample',
  tags: ['autodocs'],
  render: (args) => {
    return html`
        <iai-lit-csr-example
        ></iai-lit-csr-example>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary = {};