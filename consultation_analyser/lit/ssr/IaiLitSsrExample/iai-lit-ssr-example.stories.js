import { html } from 'lit';
import IaiLitSsrExample from './iai-lit-ssr-example.lit.ssr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Ssr/IaiLitSsrExample',
  tags: ['autodocs'],
  render: (args) => {
    return html`
      <iai-lit-ssr-example
        .encprops=${btoa(JSON.stringify({foo: args.foo}))}
      ></iai-lit-ssr-example>
    `
  },
  argTypes: {
    foo: {
      control: { type: 'select' },
      options: ['bar', 'baz'],
    },
  }
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const WithoutProps = {};

export const WithProps = {
  args: {
    foo: "bar",
  }
};