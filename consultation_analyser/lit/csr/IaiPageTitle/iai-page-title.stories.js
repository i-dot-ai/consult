import { html } from 'lit';

import IaiPageTitle from './iai-page-title.lit.csr.mjs';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/PageTitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-page-title
        .title=${args.title}
        .subtitle=${args.subtitle}
      ></iai-page-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    subtitle: "Test Subtitle",
  },
};

export const LongStrings = {
  args: {
    title: "Test Title".repeat(10),
    subtitle: "Test Subtitle".repeat(10),
  },
};

export const EmptyStrings = {
  args: {
    title: "",
    subtitle: "",
  },
};

