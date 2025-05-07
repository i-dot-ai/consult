import { html } from 'lit';
import IaiExpandingText from './iai-expanding-text.lit.csr.mjs';

const SHORT_TEXT = "Lorem ipsum";
const LONG_TEXT = "Vestibulum ut velit a mauris consequat suscipit. Morbi sit amet quam mi. Aliquam ultricies fringilla sapien, consequat vehicula nunc vehicula id. Pellentesque eu ultricies nisl. Nam non pulvinar leo. Integer sed mauris sodales, dignissim nisl et, placerat sapien. Suspendisse nec convallis turpis, tempor efficitur mi. Etiam euismod pulvinar scelerisque. Fusce eu lacus et nulla pharetra condimentum. Sed sem mi, viverra ac pulvinar sed, vestibulum vel est. Phasellus ac pretium turpis, cursus facilisis erat. Etiam commodo euismod commodo. Aliquam sodales lacus non pellentesque consequat. Donec accumsan a felis eget mattis.";

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/IaiExpandingText',
  tags: ['autodocs'],
  argTypes: {
    text: { control: { type: 'text' } },
    lines: { control: { type: "number" } }
  },
  render: (args) => {
    return html`
      <iai-expanding-text
        text=${args.text}
        lines=${args.lines}
      ></iai-expanding-text>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const SingleLineLongText = {
  args: {
    text: LONG_TEXT,
    lines: 1
  }
};

export const TripleLineLongText = {
  args: {
    text: LONG_TEXT,
    lines: 3
  }
};


export const SingleLineShortText = {
  args: {
    text: SHORT_TEXT,
    lines: 1
  }
};


export const TripleLineShortText = {
  args: {
    text: SHORT_TEXT,
    lines: 3
  }
};

export const MultipleTexts = {
  args: {
    text: LONG_TEXT
  },
  render: (args) => {
    const numInstances = 3;

    return html`
    ${[...Array(numInstances).keys()].map((_, index) => (
      html`
        <h3>Lines Allowed: ${index + 1}</h3>
        <iai-expanding-text
          text=${args.text}
          lines=${index + 1}
        ></iai-expanding-text>
      `
    ))}
      
    `
  }
};