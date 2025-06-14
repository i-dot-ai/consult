import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiVirtualList from './iai-virtual-list.lit.csr.mjs';
import { expect, fn, waitFor, within } from '@storybook/test';


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
    renderItem: (response) => html`<li>Response ${response}</li>`,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    await waitFor(() => {
      if (!canvasElement.querySelector("lit-virtualizer li")) {
        throw new Error("awaiting render");
      }
    }, {timeout: 2000});

    const responseOne = canvas.getByText("Response 1");
    expect(responseOne).toBeInTheDocument();

    const responseNineHundred = canvas.queryByText("Response 900");
    expect(responseNineHundred).toBe(null);
  }
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
      <li data-testid=${`response-${index}`} class=${index === 99 ? "last-item" : ""}>
        Response ${response}
      </li>
    `,
    handleScrollEnd: () => action("Scroll end reached")()
  },
  play: async ({ canvasElement, args }) => {
    const iaiVirtualListElement = canvasElement.querySelector("iai-virtual-list")
    iaiVirtualListElement.handleScrollEnd = fn();

    const canvas = within(canvasElement);

    await waitFor(() => {
      if (!canvasElement.querySelector("lit-virtualizer li")) {
        throw new Error("awaiting render");
      }
    }, {timeout: 2000});

    const scrollEndCallback = args.handleScrollEnd;
    expect(scrollEndCallback).toBeDefined();

    const virtualizerElement = canvasElement.querySelector("lit-virtualizer");
    virtualizerElement.scrollTop = virtualizerElement.scrollHeight;
    virtualizerElement.dispatchEvent(new Event("scroll"));

    await waitFor(() => {
      expect(iaiVirtualListElement.handleScrollEnd).toHaveBeenCalled();
    }, {timeout: 2000});

    expect(iaiVirtualListElement.handleScrollEnd).toHaveBeenCalled();

    const responseNinetyNine = canvas.queryByText("Response 99");
    expect(responseNinetyNine).toBeInTheDocument();
  },
  parameters: {
    test: {
      dangerouslyIgnoreUnhandledErrors: true
    }
  }
};