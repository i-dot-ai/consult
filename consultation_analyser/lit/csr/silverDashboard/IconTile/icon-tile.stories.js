import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IconTile from './icon-tile.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/IconTile',
  tags: ['autodocs'],
  argTypes: {
    color: { control: "color" },
    backgroundColor: { control: "color" },
  },
  render: (args) => {
    return html`
      <iai-silver-icon-tile
        .backgroundColor=${args.backgroundColor}
        .color=${args.color}
        .name=${args.name}
      ></iai-silver-icon-tile>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    backgroundColor: "var(--iai-silver-color-teal-light)",
    color: "var(--iai-silver-color-teal)",
    name: "diamond",
  },
};
