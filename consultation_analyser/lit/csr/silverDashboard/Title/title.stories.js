import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import Title from './title.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/SilverDashboard/Title',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-silver-title
        .text=${args.text}
        .subtext=${args.subtext}
        .level=${args.level}
        .icon=${args.icon}
      ></iai-silver-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    level: 2,
    text: "Test Title",
    subtext: "",
    icon: "",
  },
};

export const WithSubtext = {
  args: {
    level: 2,
    text: "Test Title",
    subtext: "Test subtext for the title",
    variant: "primary",
    icon: "",
  },
};

export const WithIcon = {
  args: {
    level: 2,
    text: "Test Title",
    subtext: "",
    variant: "primary",
    icon: "diamond",
  },
};

export const WithSubtextAndIcon = {
  args: {
    level: 2,
    text: "Test Title",
    subtext: "Test subtext for the title",
    variant: "primary",
    icon: "diamond",
  },
};

export const LevelOne = {
  args: {
    level: 1,
    text: "Test Title",
    subtext: "Test subtext for the title",
    variant: "primary",
    icon: "diamond",
  },
};

export const LevelThree = {
  args: {
    level: 3,
    text: "Test Title",
    subtext: "Test subtext for the title",
    variant: "primary",
    icon: "diamond",
  },
};