import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import Tag from './tag.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/Tag',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-tag
        .status=${args.status}
        .text=${args.text}
        .subtext=${args.subtext}
        .icon=${args.icon}
      ></iai-silver-tag>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Open = {
  args: {
    status: "Open",
    text: "Open",
    icon: "star",
  },
};

export const Closed = {
  args: {
    status: "Closed",
    text: "Closed",
    icon: "help",
  },
};

export const WithSubtext = {
  args: {
    status: "Closed",
    text: "Closed",
    subtext: "This is closed",
    icon: "help",
  },
};
