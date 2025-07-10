import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import TabView from './tab-view.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/TabView',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-tab-view
        .tabs=${args.tabs}
      ></iai-tab-view>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    tabs: [
      {
        title: "Tab 1",
        content: `<span style="color:red;">Tab 1 content</span>`,
      },
      {
        title: "Tab 2",
        content: `Tab 1 content`,
      }
    ],
  },
};
