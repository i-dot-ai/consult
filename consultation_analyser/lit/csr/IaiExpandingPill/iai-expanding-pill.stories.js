import { html } from 'lit';

import IaiExpandingPill from './iai-expanding-pill.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ExpandingPill',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-expanding-pill
        .label=${args.label}
        .body=${args.body}
        .initialExpanded=${args.initialExpanded}
      ></iai-expanding-pill>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const InitiallyExpanded = {
  args: {
    label: "Test Label",
    body: "Test body",
    initialExpanded: true,
  },
};

export const InitiallyCollapsed = {
  args: {
    label: "Test Label",
    body: "Test body",
    initialExpanded: false,
  },
};

export const LongStrings = {
  args: {
    label: "Test Label".repeat(10),
    body: "Test body".repeat(30),
    initialExpanded: true,
  },
};

export const EmptyStrings = {
  args: {
    label: "",
    body: "",
    initialExpanded: true,
  },
};
