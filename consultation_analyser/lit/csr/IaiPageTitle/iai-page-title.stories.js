import { html } from 'lit';

import { within, expect } from '@storybook/test';

import IaiPageTitle from './iai-page-title.lit.csr.mjs';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/PageTitle',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-page-title
        .title=${args.title}
        .subtitle=${args.subtitle}
      ></iai-page-title>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    title: "Test Title",
    subtitle: "Test Subtitle",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const titleElement = canvas.getByText("Test Title");
    expect(titleElement).toBeInTheDocument();

    const subtitleElement = canvas.getByText("Test Subtitle");
    expect(subtitleElement).toBeInTheDocument();
  }
};

export const LongStrings = {
  args: {
    title: "Test Title".repeat(10),
    subtitle: "Test Subtitle".repeat(10),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const titleElement = canvas.getByText("Test Title".repeat(10));
    expect(titleElement).toBeInTheDocument();

    const subtitleElement = canvas.getByText("Test Subtitle".repeat(10));
    expect(subtitleElement).toBeInTheDocument();
  }
};

export const EmptyStrings = {
  args: {
    title: "",
    subtitle: "",
  },
  play: async ({ canvasElement }) => {
    const titleElement = canvasElement.querySelector("h1");
    expect(titleElement.innerText).toBe("");

    const subtitleElement = canvasElement.querySelector("h2");
    expect(subtitleElement.innerText).toBe("");
  }
};

