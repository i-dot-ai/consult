import { html } from 'lit';
import IaiProgressBar from './iai-progress-bar.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ProgressBar',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-progress-bar
        .value=${args.value}
        .label=${args.label}
      ></iai-progress-bar>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args

export const FullBar = {
  args: {
    value: 100,
    label: "100",
  }
};

export const EmptyBar = {
  args: {
    value: 0,
    label: "0",
  }
};

export const LowBar = {
  args: {
    value: 20,
    label: "20",
  }
};

export const HighBar = {
  args: {
    value: 90,
    label: "90",
  }
};

export const DifferentBar = {
  args: {
    value: 40,
    label: "8000",
  }
};

export const StringLabelBar = {
  args: {
    value: 80,
    label: "Test Label",
  }
};