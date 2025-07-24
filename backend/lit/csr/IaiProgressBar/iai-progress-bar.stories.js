import { html } from 'lit';
import IaiProgressBar from './iai-progress-bar.lit.csr.mjs';
import { expect, within } from '@storybook/test';


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
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("100%");

    const labelElement = canvas.getByText("100");
    expect(labelElement).toBeInTheDocument();
  }
};

export const EmptyBar = {
  args: {
    value: 0,
    label: "0",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("0%");

    const labelElement = canvas.getByText("0");
    expect(labelElement).toBeInTheDocument();
  }
};

export const LowBar = {
  args: {
    value: 20,
    label: "20",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("20%");

    const labelElement = canvas.getByText("20");
    expect(labelElement).toBeInTheDocument();

    const lowValueElement = canvasElement.querySelector(".low-value");
    expect(lowValueElement).toBeInTheDocument();
  }
};

export const HighBar = {
  args: {
    value: 90,
    label: "90",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("90%");

    const labelElement = canvas.getByText("90");
    expect(labelElement).toBeInTheDocument();

    const lowValueElement = canvasElement.querySelector(".low-value");
    expect(lowValueElement).toBe(null);
  }
};

export const DifferentBar = {
  args: {
    value: 40,
    label: "8000",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("40%");

    const labelElement = canvas.getByText("8000");
    expect(labelElement).toBeInTheDocument();
  }
};

export const StringLabelBar = {
  args: {
    value: 80,
    label: "Test Label",
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const barElement = canvasElement.querySelector(".bar");
    expect(barElement.style.width).toBe("80%");

    const labelElement = canvas.getByText("Test Label");
    expect(labelElement).toBeInTheDocument();
  }
};