import { html } from 'lit';

import IaiMultiResponseItem from './iai-multi-response-item.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/MultiResponseItem',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-multi-response-item
        .countName=${args.countName}
        .countValue=${args.countValue}
        .totalCounts=${args.totalCounts}
      ></iai-multi-response-item>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    countName: "Test Count",
    countValue: 10,
    totalCounts: 100,
  },
};

export const Zero = {
  args: {
    countName: "Test Count",
    countValue: 0,
    totalCounts: 100,
  },
};

export const Full = {
  args: {
    countName: "Test Count",
    countValue: 100,
    totalCounts: 100,
  },
};

export const EmptyLabel = {
  args: {
    countName: "",
    countValue: 0,
    totalCounts: 100,
  },
};