import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiVirtualList from './iai-virtual-list.lit.csr.mjs';


const TEST_RESPONSES = [
  {
    text: "Test Response 1"
  },
  {
    text: "Test Response 2"
  },
];


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/VirtualList',
  tags: ['autodocs'],
  argTypes: {
    message: { control: "text" },
  },
  render: (args) => {
    return html`
      <iai-virtual-list
        .data=${args.data}
        .renderItem=${args.renderItem}
        .message=${args.message}
        .handleScrollEnd=${args.handleScrollEnd}
      ></iai-virtual-list>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    data: TEST_RESPONSES,
    renderItem: (response) => html`<li>${response.text}</li>`,
    message: undefined,
    handleScrollEnd: undefined,
  },
};

export const WithMessage = {
  args: {
    data: TEST_RESPONSES,
    renderItem: (response) => html`<li>${response.text}</li>`,
    message: "Test Message",
  },
};

export const LongList = {
  args: {
    data: Array.from(Array(1000).keys()),
    renderItem: (response) => html`<li>${response}</li>`,
  },
};

export const EmptyList = {
  args: {
    data: [],
    renderItem: (response) => html`
      <li>${response}</li>
    `,
  },
};

export const WithScrollCallback = {
  args: {
    data: Array.from(Array(100).keys()),
    renderItem: (response, index) => html`
      <li class=${index === 99 ? "last-item" : ""}>
        ${response}
      </li>
    `,
    handleScrollEnd: () => action("Scroll end reached")()
  },
};