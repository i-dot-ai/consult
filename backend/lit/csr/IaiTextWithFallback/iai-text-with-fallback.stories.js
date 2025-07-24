import { html } from 'lit';

import IaiTextWithFallback from './iai-text-with-fallback.lit.csr.mjs';

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/TextWithFallback',
  tags: ['autodocs'],
  render: (args) => {
    return html`
        <iai-text-with-fallback
          text=${args.text}
          fallback=${args.fallback}
        ></iai-text-with-fallback>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const TruthyText = {
  args: {
    text: "Text Content",
    fallback: "Fallback Text",
  }
};

export const FalsyText = {
  args: {
    text: "",
    fallback: "Fallback Text",
  }
};

export const CustomCondition = {
  args: {
    text: "Test Text 01",
    fallback: "Text cannot contain digits",
    fallbackCondition: (text) => /\d/.test(text)
  },

  render: (args) => {
    return html`
      <iai-text-with-fallback
        text=${args.text}
        fallback=${args.fallback}
        .fallbackCondition=${args.fallbackCondition}
      ></iai-text-with-fallback>
    `
  }
}