import { html } from 'lit';

import { action } from "@storybook/addon-actions";

import IaiTextInput from './iai-text-input.lit.csr.mjs';


// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
export default {
  title: 'Csr/Inputs/TextInput',
  tags: ['autodocs'],
  argTypes: {
    inputId: { control: "text" },
    name: { control: "text" },
    label: { control: "text" },
    hideLabel: { control: "boolean" },
    placeholder: { control: "text" },
    value: { control: "text" },
  },
  render: (args) => {
    return html`
      <iai-text-input
        inputId=${args.inputId}  
        name=${args.name}
        label=${args.label}
        placeholder=${args.placeholder}
        value=${args.value}
        .hideLabel=${args.hideLabel}
        .handleInput=${args.handleInput}
      ></iai-text-input>
    `
  },
};

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Default = {
  args: {
    inputId: "text-input-example",
    name: "text-input-example",
    label: "Text Input Example",
    placeholder: "Enter a value...",
    value: "",
    handleInput: () => action("Text value changed to:")(event.target.value),
  }
};

export const HiddenLabel = {
  args: {
    inputId: "text-input-example",
    name: "text-input-example",
    label: "Text Input Example",
    hideLabel: true,
    placeholder: "Enter a value...",
    value: "",
    handleInput: () => action("Text value changed to:")(event.target.value),
  }
};