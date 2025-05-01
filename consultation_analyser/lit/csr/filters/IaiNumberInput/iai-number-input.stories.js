import { html } from 'lit';
import { action } from "@storybook/addon-actions";

import IaiNumberInput from './iai-number-input.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/IaiNumberInput',
  tags: ['autodocs'],
  argTypes: {
    inputId: { control: "text" },
    name: { control: "text" },
    label: { control: "text" },
    placeholder: { control: "text" },
    value: { control: "number" },
  },
  render: (args) => {
    return html`
      <iai-number-input
        inputId=${args.inputId}  
        name=${args.name}
        label=${args.label}
        placeholder=${args.placeholder}
        value=${args.value}
        .handleInput=${args.handleInput}
      ></iai-number-input>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    inputId: "number-input-example",
    name: "number-input-example",
    label: "Number Input Example",
    placeholder: "Enter a value...",
    value: null,
    handleInput: () => action("Number value changed to:")(event.target.value),
  }
};