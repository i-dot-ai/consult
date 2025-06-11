import { html } from 'lit';

import IaiLoadingIndicator from './iai-loading-indicator.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/LoadingIndicator',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-loading-indicator></iai-loading-indicator>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args

export const Default = {
  args: {}
};
