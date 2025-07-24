import { html } from 'lit';

import IaiResponsesTitle from './iai-responses-title.lit.csr.mjs';
import { expect, within } from '@storybook/test';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ResponsesDashboard/ResponsesTitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-responses-title
        .total=${args.total}
      ></iai-responses-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    total: 100,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const numberElement = canvas.getByText("100 responses");
    expect(numberElement).toBeInTheDocument();

    const titleElement = canvas.getByText("Individual responses");
    expect(titleElement).toBeInTheDocument();
  }
};

export const ZeroTotal = {
  args: {
    total: 0,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const numberElement = canvas.getByText("0 responses");
    expect(numberElement).toBeInTheDocument();
  }
};

export const LargeTotal = {
  args: {
    total: 100000,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const numberElement = canvas.getByText("100000 responses");
    expect(numberElement).toBeInTheDocument();
  }
};

export const NegativeTotal = {
  args: {
    total: -10,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const numberElement = canvas.getByText("-10 responses");
    expect(numberElement).toBeInTheDocument();
  }
};