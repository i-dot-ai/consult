import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiResponses from './iai-responses.mjs';


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
  title: 'Csr/Responses',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-responses
        .responses=${args.responses}
        .renderResponse=${args.renderResponse}
        .message=${args.message}
        .handleScrollEnd=${args.handleScrollEnd}
      ></iai-responses>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    responses: TEST_RESPONSES,
    renderResponse: (response) => html`<li>${response.text}</li>`,
  },
};

export const WithMessage = {
  args: {
    responses: TEST_RESPONSES,
    renderResponse: (response) => html`<li>${response.text}</li>`,
    message: "Test Message",
  },
};

export const LongList = {
  args: {
    responses: Array.from(Array(1000).keys()),
    renderResponse: (response) => html`<li>${response}</li>`,
  },
};

export const WithScrollCallback = {
  args: {
    responses: Array.from(Array(100).keys()),
    renderResponse: (response, index) => html`
      <li class=${index === 99 ? "last-response" : ""}>
        ${response}
      </li>
    `,
    handleScrollEnd: () => action("Scroll end reached")()
  },
};