import { html } from 'lit';

import IaiIcon from './iai-icon.mjs';
import { expect, within } from '@storybook/test';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Icon',
  tags: ['autodocs'],
  argTypes: {
    name: {
      control: { type: "select" },
      options: ["visibility", "close", "star", "search", "thumb_up", "thumb_down", "thumbs_up_down", "arrow_drop_down_circle", "download", "diamond", "progress_activity", "sort"],
    },
    color: {
      control: { type: "color" },
    }
  },
  render: (args) => {
    return html`
      <iai-icon
        .name=${args.name}
        .opsz=${args.opsz}
        .color=${args.color}
        .fill=${args.fill}
        .wght=${args.wght}
      ></iai-icon>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    name: "thumb_up",
    opsz: 12,
    color: "red",
    fill: true,
    wght: 300,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const iconElement = canvas.getByText("thumb_up");
    expect(iconElement).toBeInTheDocument();
  }
};