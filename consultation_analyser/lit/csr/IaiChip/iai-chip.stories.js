import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiChip from './iai-chip.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Chip',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-chip
        .label=${args.label}
        .handleClick=${args.handleClick}
      ></iai-chip>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    label: "Test Label",
    handleClick: action("Chip was clicked on"),
  },
};

export const EmptyLabel = {
  args: {
    label: "",
    handleClick: action("Chip was clicked on"),
  },
};

export const LongLabel = {
  args: {
    label: "Test Label".repeat(10),
    handleClick: action("Chip was clicked on"),
  },
};