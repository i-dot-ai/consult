import { html } from 'lit';

import IaiTextResponseItem from './iai-text-response-item.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/QuestionsArchive/TextResponseItem',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-text-response-item
        .iconName=${args.iconName}
        .text=${args.text}
      ></iai-text-response-item>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Agree = {
  args: {
    iconName: "thumb_up",
    text: "Test response item",
  },
};

export const Disagree = {
  args: {
    iconName: "thumb_down",
    text: "Test response item",
  },
};

export const Unclear = {
  args: {
    iconName: "thumbs_up_down",
    text: "Test response item",
  },
};
