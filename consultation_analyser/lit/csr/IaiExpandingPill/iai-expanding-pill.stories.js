import { html } from 'lit';

import IaiExpandingPill from './iai-expanding-pill.lit.csr.mjs';
import { expect, within } from '@storybook/test';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/ExpandingPill',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-expanding-pill
        .label=${args.label}
        .body=${args.body}
        .initialExpanded=${args.initialExpanded}
      ></iai-expanding-pill>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const InitiallyExpanded = {
  args: {
    label: "Test Label",
    body: "Test body",
    initialExpanded: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    const labelElement = canvas.getByText("Test Label");
    expect(labelElement).toBeInTheDocument();

    const bodyElement = canvas.getByText("Test body");
    expect(bodyElement).toBeInTheDocument();

    const expandedElement = canvasElement.querySelector(".expanded");
    expect(expandedElement).toBeInTheDocument();
  }
};

export const InitiallyCollapsed = {
  args: {
    label: "Test Label",
    body: "Test body",
    initialExpanded: false,
  },
  play: async ({ canvasElement }) => {
    const expandedElement = canvasElement.querySelector(".expanded");
    expect(expandedElement).toBe(null);
  }
};

export const LongStrings = {
  args: {
    label: "Test Label".repeat(10),
    body: "Test body".repeat(30),
    initialExpanded: true,
  },
  play: async ({ canvasElement }) => {
    const buttonElement = canvasElement.querySelector("button")
    expect(buttonElement.innerText).toContain("Test Label".repeat(10));

    const bodyElement = canvasElement.querySelector(".body")
    expect(bodyElement.innerText).toContain("Test body".repeat(30));
  }
};

export const EmptyStrings = {
  args: {
    label: "",
    body: "",
    initialExpanded: true,
  },
  play: async ({ canvasElement }) => {
    const buttonElement = canvasElement.querySelector("button")
    expect(buttonElement.innerText).toBe("arrow_drop_down_circle");

    const bodyElement = canvasElement.querySelector(".body")
    expect(bodyElement.innerText).toContain("");
  }
};
